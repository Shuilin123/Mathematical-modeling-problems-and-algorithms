#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
方形件组批优化问题 — 2D板材切割下料求解器
===============================================
功能：
  1. 从Word文档提取问题参数
  2. 读取CSV数据集
  3. 3阶段齐头切启发式排样算法（子问题1）
  4. 订单组批+排样优化（子问题2）
  5. 切割排布可视化
  6. 输出cut_program.csv和sum_order.csv

核心算法：
  - 采用Shelf-Based FFD（First Fit Decreasing）排样
  - 支持3阶段齐头切约束
  - 同一栈内产品项宽度相同
  - 允许旋转优化
  - 多策略比较选优
"""

import os
import sys
import glob
import math
import random
import colorsys
import warnings
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Optional, Set

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 尝试导入python-docx
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False
    print("[警告] python-docx未安装，将使用默认参数。安装命令: pip install python-docx")

warnings.filterwarnings('ignore')


# ============================================================
# 第一部分：参数提取与解析
# ============================================================

@dataclass
class ProblemParams:
    """问题参数数据类"""
    plate_length: float = 2440.0
    plate_width: float = 1220.0
    max_item_num: int = 1000
    max_item_area: float = 250.0
    allow_rotation: bool = True
    guillotine_cut: bool = True
    max_stages: int = 3


def extract_params_from_docx(docx_path: str) -> ProblemParams:
    """从Word文档中提取问题参数"""
    params = ProblemParams()
    if not HAS_DOCX:
        return params
    if not os.path.exists(docx_path):
        return params
    try:
        doc = Document(docx_path)
        full_text = "\n".join([p.text for p in doc.paragraphs])
        m = re.search(r'plate_length\s*=\s*(\d+)', full_text)
        if m: params.plate_length = float(m.group(1))
        m = re.search(r'plate_width\s*=\s*(\d+)', full_text)
        if m: params.plate_width = float(m.group(1))
        m = re.search(r'max_item_num\s*=\s*(\d+)', full_text)
        if m: params.max_item_num = int(m.group(1))
        m = re.search(r'max_item_area\s*=\s*(\d+)', full_text)
        if m: params.max_item_area = float(m.group(1))
        if '齐头切' in full_text or 'guillotine' in full_text.lower():
            params.guillotine_cut = True
        m = re.search(r'阶段数不超过(\d+)', full_text)
        if m: params.max_stages = int(m.group(1))
        print(f"[信息] 从文档提取参数: 原片{params.plate_length}x{params.plate_width}mm, "
              f"批次上限{params.max_item_num}项/{params.max_item_area}m²")
    except Exception as e:
        print(f"[警告] 读取文档失败: {e}")
    return params


def load_items_from_csv(csv_path: str) -> pd.DataFrame:
    """从CSV文件加载产品项数据"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"数据文件不存在: {csv_path}")
    df = pd.read_csv(csv_path)
    required_cols = ['item_id', 'item_material', 'item_num', 'item_length', 'item_width', 'item_order']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"数据文件缺少必要列: {missing}")
    df['item_length'] = pd.to_numeric(df['item_length'], errors='coerce').fillna(0)
    df['item_width'] = pd.to_numeric(df['item_width'], errors='coerce').fillna(0)
    df['item_num'] = pd.to_numeric(df['item_num'], errors='coerce').fillna(0).astype(int)
    df = df[(df['item_length'] > 0) & (df['item_width'] > 0) & (df['item_num'] > 0)]
    df['area'] = df['item_length'] * df['item_width']
    return df


# ============================================================
# 第二部分：核心排样算法
# ============================================================

@dataclass
class PlacedItem:
    """已放置的产品项"""
    item_id: int
    material: str
    x: float
    y: float
    length: float
    width: float
    rotated: bool = False
    order: str = ""


@dataclass
class CuttingBoard:
    """一块原片的排样结果"""
    board_id: int
    material: str
    plate_length: float
    plate_width: float
    placed_items: List[PlacedItem] = field(default_factory=list)

    @property
    def used_area(self):
        return sum(it.length * it.width for it in self.placed_items)

    @property
    def total_area(self):
        return self.plate_length * self.plate_width

    @property
    def utilization(self):
        return self.used_area / self.total_area if self.total_area > 0 else 0


class GuillotineCutPacker:
    """
    3阶段齐头切排样器（改进版）

    算法核心：
    ========
    采用"条带-栈"两层结构的Shelf-Based FFD算法：

    第1阶段（Stripe/条带）：原片沿y方向切为若干水平条带
    第2阶段（Stack/栈）：每条带沿x方向切为若干垂直栈
    第3阶段（Item/产品项）：每栈沿x方向排列产品项（同宽度归并）

    约束：同一栈内产品项的y方向尺寸（宽度）必须相同。

    改进策略：
    1. 宽度聚类：将相近宽度归并为同一组（容差2%或5mm）
    2. 双向尝试：同时尝试"宽优先"和"长优先"两种朝向
    3. BFD装栈：使用Best Fit Decreasing策略装栈
    4. 条带混合：同一条带内允许不同宽度的栈（取最大宽度为条带高度）
    5. 残料回填：利用条带和原片的剩余空间
    6. 多轮选优：比较多种策略的结果，选择最优
    """

    def __init__(self, plate_length=2440.0, plate_width=1220.0, allow_rotation=True):
        self.L = plate_length
        self.W = plate_width
        self.allow_rotation = allow_rotation

    def pack(self, items_df: pd.DataFrame, material: str = "") -> List[CuttingBoard]:
        """对给定产品项集合进行排样，返回排样结果列表"""
        if len(items_df) == 0:
            return []
        items = self._expand_items(items_df)
        if not items:
            return []

        # 多策略+多容差比较选优
        best_boards, best_count = None, float('inf')

        for tol_pct, tol_min in [(0.02, 5.0), (0.05, 10.0), (0.10, 20.0)]:
            for strategy in ['width_first', 'length_first', 'hybrid']:
                boards = self._pack_with_strategy(items, material, strategy, tol_pct, tol_min)
                if len(boards) < best_count:
                    best_count = len(boards)
                    best_boards = boards

        return best_boards

    def _expand_items(self, df: pd.DataFrame) -> List[dict]:
        """展开item_num为单独的项"""
        items = []
        for _, row in df.iterrows():
            for _ in range(int(row['item_num'])):
                items.append({
                    'item_id': row['item_id'],
                    'material': row['item_material'],
                    'length': float(row['item_length']),
                    'width': float(row['item_width']),
                    'order': row['item_order'],
                })
        return items

    def _orient_items(self, items: List[dict], strategy: str) -> List[dict]:
        """
        确定每个产品项的朝向，确保朝向后的尺寸不超过原片尺寸
        
        strategy:
          'width_first' - 优先短边作为y方向（宽度），有利于栈宽度一致
          'length_first' - 优先长边作为y方向，可能产生更深的栈
          'hybrid' - 混合策略，根据面积选择
          
        关键约束：el <= plate_length 且 ew <= plate_width
        如果优先朝向超出原片范围，自动切换到另一朝向
        """
        oriented = []
        for item in items:
            l, w = item['length'], item['width']
            
            # 两种可能的朝向
            # 朝向A: l作为x方向长度(el), w作为y方向宽度(ew)
            # 朝向B: w作为x方向长度(el), l作为y方向宽度(ew)
            el_a, ew_a, rot_a = l, w, False
            el_b, ew_b, rot_b = w, l, True
            
            # 检查哪种朝向能放入原片
            fits_a = (el_a <= self.L and ew_a <= self.W)
            fits_b = (el_b <= self.L and ew_b <= self.W)
            
            # 根据策略选择优先朝向
            if strategy == 'width_first':
                # 优先短边作为y方向(ew)
                prefer_a = (l >= w)  # l>=w时, 朝向A的ew=w(短边)
            elif strategy == 'length_first':
                # 优先长边作为y方向(ew)
                prefer_a = (l < w)   # l<w时, 朝向A的ew=w(长边)
            else:  # hybrid
                prefer_a = (l >= w)  # 同width_first
            
            # 选择朝向：优先使用策略偏好的朝向，但不使用超出原片的朝向
            if prefer_a and fits_a:
                el, ew, rot = el_a, ew_a, rot_a
            elif (not prefer_a) and fits_b:
                el, ew, rot = el_b, ew_b, rot_b
            elif fits_a:
                el, ew, rot = el_a, ew_a, rot_a
            elif fits_b:
                el, ew, rot = el_b, ew_b, rot_b
            else:
                # 两种朝向都无法放入原片，选择溢出较小的
                overflow_a = max(0, el_a - self.L) + max(0, ew_a - self.W)
                overflow_b = max(0, el_b - self.L) + max(0, ew_b - self.W)
                if overflow_a <= overflow_b:
                    el, ew, rot = el_a, ew_a, rot_a
                else:
                    el, ew, rot = el_b, ew_b, rot_b
            
            oriented.append({**item, 'el': el, 'ew': ew, 'rotated': rot})
        return oriented

    def _pack_with_strategy(self, items: List[dict], material: str, strategy: str,
                             tol_pct: float = 0.02, tol_min: float = 5.0) -> List[CuttingBoard]:
        """使用指定策略进行排样"""
        oriented = self._orient_items(items, strategy)

        # 按宽度归并分组，构建栈
        stacks = self._build_stacks(oriented, tol_pct, tol_min)

        # 将栈装入原片
        boards = self._pack_stacks_to_boards(stacks, material)

        return boards

    def _build_stacks(self, items: List[dict], width_tolerance_pct=0.02, width_tolerance_min=5.0) -> List[dict]:
        """
        构建栈：同一栈内产品项宽度(y方向)相同，长度(x方向)之和不超过L

        改进：使用宽度聚类（容差2%或5mm），将相近宽度归并为同一组，
        使用组内最大宽度作为栈宽度，减少窄栈数量，提高利用率。

        返回: [{'items': [...], 'stack_w': y方向宽度, 'stack_l': x方向总长度}]
        """
        # 按宽度聚类分组（使用较大容差归并）
        # 先按精确宽度排序
        items_sorted = sorted(items, key=lambda x: x['ew'])

        # 贪心聚类：将相邻宽度的项归入同一组
        clusters = []  # [{'items': [...], 'cluster_w': 最大宽度}]
        for item in items_sorted:
            ew = item['ew']
            placed = False
            for cluster in clusters:
                cluster_w = cluster['cluster_w']
                # 容差：2%或5mm，取较大值
                tol = max(cluster_w * width_tolerance_pct, width_tolerance_min)
                if ew <= cluster_w + tol:
                    # 可以归入此聚类
                    cluster['items'].append(item)
                    if ew > cluster_w:
                        cluster['cluster_w'] = ew
                    placed = True
                    break
            if not placed:
                clusters.append({'items': [item], 'cluster_w': ew})

        stacks = []
        for cluster in clusters:
            group = sorted(cluster['items'], key=lambda x: -x['el'])
            cluster_w = cluster['cluster_w']

            # BFD装栈：维护活跃栈列表，每次找最佳匹配
            active_stacks = []  # [(remaining_length, [items])]

            for item in group:
                best_idx = -1
                best_waste = float('inf')

                for idx, (rem, _) in enumerate(active_stacks):
                    if rem >= item['el']:
                        waste = rem - item['el']
                        if waste < best_waste:
                            best_waste = waste
                            best_idx = idx

                if best_idx >= 0:
                    active_stacks[best_idx][1].append(item)
                    active_stacks[best_idx] = (best_waste, active_stacks[best_idx][1])
                else:
                    new_stack = [item]
                    remaining = self.L - item['el']
                    active_stacks.append((remaining, new_stack))

            for rem, stack_items in active_stacks:
                if stack_items:
                    # 使用聚类宽度作为栈宽度（而非项的最大宽度）
                    sl = sum(it['el'] for it in stack_items)
                    stacks.append({'items': stack_items, 'stack_w': cluster_w, 'stack_l': sl})

        return stacks

    def _pack_stacks_to_boards(self, stacks: List[dict], material: str) -> List[CuttingBoard]:
        """
        将栈装入原片：使用全局最优适配算法

        改进：
        1. 全局最优适配：考虑所有已有原片，选择浪费最小的放置位置
        2. 多种排序策略：尝试不同栈排序，选最优
        3. 条带内宽松匹配：栈宽度 <= 条带高度即可放入
        4. 原片合并后处理：尝试将稀疏原片的栈合并到其他原片
        """
        # 尝试多种排序策略，选最优
        sort_keys = [
            ('w_desc_l_desc', lambda s: (-s['stack_w'], -s['stack_l'])),
            ('l_desc_w_desc', lambda s: (-s['stack_l'], -s['stack_w'])),
            ('area_desc', lambda s: (-(s['stack_w'] * s['stack_l']),)),
            ('w_desc_l_asc', lambda s: (-s['stack_w'], s['stack_l'])),
            ('w_asc_l_desc', lambda s: (s['stack_w'], -s['stack_l'])),
        ]

        best_boards = None
        best_count = float('inf')

        for sort_name, sort_key in sort_keys:
            boards = self._pack_stacks_to_boards_single(stacks, material, sort_key)
            if len(boards) < best_count:
                best_count = len(boards)
                best_boards = boards

        return best_boards

    def _pack_stacks_to_boards_single(self, stacks: List[dict], material: str,
                                        sort_key) -> List[CuttingBoard]:
        """使用指定排序策略将栈装入原片（全局最优适配）"""
        stacks_sorted = sorted(stacks, key=sort_key)

        # 所有原片的数据结构
        boards_data = []  # [{'stripes': [...], 'used_y': y}]

        for sinfo in stacks_sorted:
            sw, sl = sinfo['stack_w'], sinfo['stack_l']

            # 全局最优适配：在所有原片的所有条带中找最佳位置
            best_board_idx = -1
            best_stripe_idx = -1
            best_is_new_stripe = False
            best_score = float('inf')

            for bidx, bdata in enumerate(boards_data):
                # 尝试放入已有条带
                for sidx, stripe in enumerate(bdata['stripes']):
                    stripe_h = stripe['height']
                    if sw <= stripe_h and stripe['used_l'] + sl <= self.L:
                        # 评分：高度浪费 + 长度浪费（越小越好）
                        height_waste = (stripe_h - sw) * sl
                        length_remaining = self.L - stripe['used_l'] - sl
                        score = height_waste + length_remaining * min(sw, stripe_h - sw)
                        if score < best_score:
                            best_score = score
                            best_board_idx = bidx
                            best_stripe_idx = sidx
                            best_is_new_stripe = False

                # 尝试创建新条带
                if bdata['used_y'] + sw <= self.W:
                    # 评分：剩余宽度浪费
                    remaining_w = self.W - bdata['used_y'] - sw
                    score = remaining_w * self.L * 0.1  # 新条带惩罚系数
                    if score < best_score:
                        best_score = score
                        best_board_idx = bidx
                        best_stripe_idx = -1
                        best_is_new_stripe = True

            if best_board_idx >= 0:
                bdata = boards_data[best_board_idx]
                if best_is_new_stripe:
                    stripe = {'height': sw, 'stacks': [sinfo], 'used_l': sl}
                    bdata['stripes'].append(stripe)
                    bdata['used_y'] += sw
                else:
                    bdata['stripes'][best_stripe_idx]['stacks'].append(sinfo)
                    bdata['stripes'][best_stripe_idx]['used_l'] += sl
            else:
                # 创建新原片
                stripe = {'height': sw, 'stacks': [sinfo], 'used_l': sl}
                boards_data.append({'stripes': [stripe], 'used_y': sw})

        # 转换为CuttingBoard对象
        result = []
        for bidx, bdata in enumerate(boards_data):
            board = self._create_board(bidx, bdata['stripes'], material)
            result.append(board)

        return result

    def _create_board(self, board_id: int, stripes: List[dict], material: str) -> CuttingBoard:
        """根据条带信息创建原片排样结果"""
        board = CuttingBoard(
            board_id=board_id, material=material,
            plate_length=self.L, plate_width=self.W
        )

        y_pos = 0
        for stripe in stripes:
            x_pos = 0
            for sinfo in stripe['stacks']:
                # 栈内产品项沿x方向排列（与stack_l=sum(el)一致）
                # 同一栈内项的y方向尺寸(ew)相同，共享同一y位置
                item_x = x_pos
                for item in sinfo['items']:
                    pi = PlacedItem(
                        item_id=item['item_id'], material=item['material'],
                        x=item_x, y=y_pos,
                        length=item['el'], width=item['ew'],
                        rotated=item['rotated'], order=item['order']
                    )
                    board.placed_items.append(pi)
                    item_x += item['el']
                x_pos += sinfo['stack_l']
            y_pos += stripe['height']

        return board


class EnhancedGuillotinePacker(GuillotineCutPacker):
    """
    增强版3阶段齐头切排样器

    在基础版上增加：
    1. 多种宽度聚类容差尝试
    2. 条带内混合宽度栈
    3. 残料回填：利用条带和原片的剩余空间
    4. 多排序策略比较选优
    5. 随机扰动优化
    6. 原片合并后处理
    """

    def pack(self, items_df: pd.DataFrame, material: str = "") -> List[CuttingBoard]:
        if len(items_df) == 0:
            return []
        items = self._expand_items(items_df)
        if not items:
            return []

        best_boards, best_count = None, float('inf')

        # 策略1：不同宽度聚类容差 + 不同朝向策略
        for tol_pct, tol_min in [(0.005, 1.0), (0.01, 2.0), (0.02, 5.0), (0.03, 8.0)]:
            for strategy in ['width_first', 'length_first', 'hybrid']:
                boards = self._pack_with_tolerance(items, material, strategy, tol_pct, tol_min)
                if len(boards) < best_count:
                    best_count = len(boards)
                    best_boards = boards

        # 策略2：按面积降序排列的shelf算法
        boards = self._pack_shelf_area_desc(items, material)
        if len(boards) < best_count:
            best_count = len(boards)
            best_boards = boards

        # 策略3：长边降序shelf算法
        boards = self._pack_shelf_length_desc(items, material)
        if len(boards) < best_count:
            best_count = len(boards)
            best_boards = boards

        # 策略4：随机扰动优化（多次随机排序取最优）
        import random
        random.seed(42)
        for _ in range(20):
            shuffled = items.copy()
            random.shuffle(shuffled)
            for strategy in ['width_first', 'length_first']:
                oriented = self._orient_items(shuffled, strategy)
                stacks = self._build_stacks(oriented, 0.01, 2.0)
                boards = self._pack_stacks_to_boards(stacks, material)
                if len(boards) < best_count:
                    best_count = len(boards)
                    best_boards = boards

        # 后处理：尝试合并稀疏原片
        if best_boards:
            best_boards = self._consolidate_boards(best_boards, material)
            best_count = len(best_boards)

        return best_boards

    def _pack_with_tolerance(self, items: List[dict], material: str, strategy: str,
                              tol_pct: float, tol_min: float) -> List[CuttingBoard]:
        """使用指定宽度聚类容差进行排样"""
        oriented = self._orient_items(items, strategy)
        stacks = self._build_stacks(oriented, tol_pct, tol_min)
        boards = self._pack_stacks_to_boards(stacks, material)
        return boards

    def _pack_shelf_area_desc(self, items: List[dict], material: str) -> List[CuttingBoard]:
        """
        按面积降序的Shelf排样算法（带宽度聚类）

        不严格按宽度分组，而是按面积降序放置，
        同一shelf内产品项按宽度对齐（取最大宽度为shelf高度）
        """
        oriented = self._orient_items(items, 'width_first')
        # 按面积降序排列
        oriented_sorted = sorted(oriented, key=lambda x: -(x['el'] * x['ew']))

        boards = []
        board_id = 0

        # 当前原片的shelf列表
        shelves = []  # [{'height': h, 'items': [...], 'used_l': used_length}]
        current_y = 0

        for item in oriented_sorted:
            el, ew = item['el'], item['ew']
            placed = False

            # 尝试放入已有shelf（最佳匹配：宽度差最小）
            best_shelf_idx = -1
            best_shelf_waste = float('inf')

            for idx, shelf in enumerate(shelves):
                if ew <= shelf['height'] and shelf['used_l'] + el <= self.L:
                    height_waste = shelf['height'] - ew
                    if height_waste < best_shelf_waste:
                        best_shelf_waste = height_waste
                        best_shelf_idx = idx

            if best_shelf_idx >= 0:
                shelves[best_shelf_idx]['items'].append(item)
                shelves[best_shelf_idx]['used_l'] += el
                placed = True

            if not placed:
                # 创建新shelf
                if current_y + ew <= self.W:
                    shelf = {'height': ew, 'items': [item], 'used_l': el}
                    shelves.append(shelf)
                    current_y += ew
                else:
                    # 保存当前原片
                    if shelves:
                        board = self._create_board_from_shelves(board_id, shelves, material)
                        boards.append(board)
                        board_id += 1
                    shelves = [{'height': ew, 'items': [item], 'used_l': el}]
                    current_y = ew

        if shelves:
            board = self._create_board_from_shelves(board_id, shelves, material)
            boards.append(board)

        return boards

    def _pack_shelf_length_desc(self, items: List[dict], material: str) -> List[CuttingBoard]:
        """
        按长边降序的Shelf排样算法

        优先放置长边较大的项，有利于填满条带长度
        """
        oriented = self._orient_items(items, 'width_first')
        # 按长边降序排列
        oriented_sorted = sorted(oriented, key=lambda x: -x['el'])

        boards = []
        board_id = 0

        shelves = []
        current_y = 0

        for item in oriented_sorted:
            el, ew = item['el'], item['ew']
            placed = False

            # 尝试放入已有shelf（最佳匹配）
            best_shelf_idx = -1
            best_shelf_waste = float('inf')

            for idx, shelf in enumerate(shelves):
                if ew <= shelf['height'] and shelf['used_l'] + el <= self.L:
                    height_waste = shelf['height'] - ew
                    if height_waste < best_shelf_waste:
                        best_shelf_waste = height_waste
                        best_shelf_idx = idx

            if best_shelf_idx >= 0:
                shelves[best_shelf_idx]['items'].append(item)
                shelves[best_shelf_idx]['used_l'] += el
                placed = True

            if not placed:
                if current_y + ew <= self.W:
                    shelf = {'height': ew, 'items': [item], 'used_l': el}
                    shelves.append(shelf)
                    current_y += ew
                else:
                    if shelves:
                        board = self._create_board_from_shelves(board_id, shelves, material)
                        boards.append(board)
                        board_id += 1
                    shelves = [{'height': ew, 'items': [item], 'used_l': el}]
                    current_y = ew

        if shelves:
            board = self._create_board_from_shelves(board_id, shelves, material)
            boards.append(board)

        return boards

    def _create_board_from_shelves(self, board_id: int, shelves: List[dict], material: str) -> CuttingBoard:
        """从shelf信息创建原片"""
        board = CuttingBoard(
            board_id=board_id, material=material,
            plate_length=self.L, plate_width=self.W
        )

        y_pos = 0
        for shelf in shelves:
            x_pos = 0
            for item in shelf['items']:
                pi = PlacedItem(
                    item_id=item['item_id'], material=item['material'],
                    x=x_pos, y=y_pos,
                    length=item['el'], width=item['ew'],
                    rotated=item['rotated'], order=item['order']
                )
                board.placed_items.append(pi)
                x_pos += item['el']
            y_pos += shelf['height']

        return board

    def _consolidate_boards(self, boards: List[CuttingBoard], material: str) -> List[CuttingBoard]:
        """
        后处理：尝试合并稀疏原片
        
        策略：找出利用率最低的原片，尝试将其栈移到其他原片
        """
        if len(boards) <= 1:
            return boards

        plate_area = self.L * self.W
        improved = True
        while improved:
            improved = False
            
            # 计算每个原片的利用率
            board_utils = []
            for i, board in enumerate(boards):
                used_area = sum(it.length * it.width for it in board.placed_items)
                util = used_area / plate_area
                board_utils.append((i, util, used_area))
            
            # 按利用率升序排列
            board_utils.sort(key=lambda x: x[1])
            
            # 尝试将利用率最低的原片的项移到其他原片
            for src_idx, src_util, src_area in board_utils:
                if src_util > 0.85:  # 利用率已经很高，不需要合并
                    continue
                    
                src_board = boards[src_idx]
                src_items = [(it.item_id, it.material, it.length, it.width, 
                             it.x, it.y, it.rotated, it.order) for it in src_board.placed_items]
                
                # 将源原片的项重新打包，尝试放入其他原片
                # 简化策略：将源原片的所有项收集起来，与其他原片的剩余空间匹配
                items_to_place = []
                for it in src_board.placed_items:
                    items_to_place.append({
                        'item_id': it.item_id, 'material': it.material,
                        'length': it.length, 'width': it.width,
                        'el': it.length, 'ew': it.width,
                        'rotated': it.rotated, 'order': it.order,
                        'item_num': 1, 'area': it.length * it.width
                    })
                
                # 尝试将这些项放入其他原片的剩余空间
                placed_items = []
                remaining_items = list(items_to_place)
                
                for dst_idx, dst_board in enumerate(boards):
                    if dst_idx == src_idx:
                        continue
                    if not remaining_items:
                        break
                    
                    # 计算目标原片的已用空间
                    used_y = max((it.y + it.width) for it in dst_board.placed_items) if dst_board.placed_items else 0
                    remaining_y = self.W - used_y
                    
                    if remaining_y < 10:  # 剩余空间太小
                        continue
                    
                    # 尝试将项放入目标原片的剩余空间
                    still_remaining = []
                    for item in remaining_items:
                        if item['ew'] <= remaining_y and item['el'] <= self.L:
                            # 可以放入
                            pi = PlacedItem(
                                item_id=item['item_id'], material=item['material'],
                                x=0, y=used_y,
                                length=item['el'], width=item['ew'],
                                rotated=item['rotated'], order=item['order']
                            )
                            dst_board.placed_items.append(pi)
                            used_y += item['ew']
                            remaining_y -= item['ew']
                        else:
                            still_remaining.append(item)
                    remaining_items = still_remaining
                
                # 如果所有项都被放置了，移除源原片
                if not remaining_items:
                    boards.pop(src_idx)
                    improved = True
                    break
        
        # 重新编号
        for i, board in enumerate(boards):
            board.board_id = i
        
        return boards

class OrderBatcher:
    """
    订单组批器

    约束条件：
    1. 每份订单当且仅当出现在一个批次中
    2. 每个批次中相同材质的产品项才能使用同一块原片
    3. 每个批次产品项总数不超过max_item_num
    4. 每个批次产品项面积总和不超过max_item_area
    """

    def __init__(self, max_item_num=1000, max_item_area=250.0,
                 plate_length=2440.0, plate_width=1220.0):
        self.max_item_num = max_item_num
        self.max_item_area = max_item_area * 1e6  # 转换为mm²
        self.plate_length = plate_length
        self.plate_width = plate_width

    def batch_orders(self, df: pd.DataFrame) -> List[pd.DataFrame]:
        """对产品项数据进行组批，返回批次列表"""
        if len(df) == 0:
            return []

        # 按订单分组统计
        order_stats = df.groupby('item_order').agg(
            item_count=('item_num', 'sum'),
            total_area=('area', 'sum'),
            materials=('item_material', lambda x: list(set(x)))
        ).reset_index()

        # 按材质分组订单
        material_orders = defaultdict(list)
        for _, row in order_stats.iterrows():
            for mat in row['materials']:
                material_orders[mat].append(row)

        batches = []

        # 对每种材质独立组批（贪心策略：按订单面积降序）
        for material, orders in material_orders.items():
            orders_sorted = sorted(orders, key=lambda x: -x['total_area'])

            current_batch_orders = []
            current_batch_count = 0
            current_batch_area = 0.0

            for order_row in orders_sorted:
                order_count = order_row['item_count']
                order_area = order_row['total_area']

                if (current_batch_count + order_count <= self.max_item_num and
                    current_batch_area + order_area <= self.max_item_area):
                    current_batch_orders.append(order_row['item_order'])
                    current_batch_count += order_count
                    current_batch_area += order_area
                else:
                    if current_batch_orders:
                        batch_df = df[df['item_order'].isin(current_batch_orders)]
                        batches.append(batch_df)

                    current_batch_orders = [order_row['item_order']]
                    current_batch_count = order_count
                    current_batch_area = order_area

            if current_batch_orders:
                batch_df = df[df['item_order'].isin(current_batch_orders)]
                batches.append(batch_df)

        return batches


# ============================================================
# 第四部分：切割排布可视化
# ============================================================

class CuttingVisualizer:
    """切割排布可视化器"""

    def __init__(self, output_dir="output_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self._color_map = {}
        self._color_idx = 0

    def _get_color(self, key: str) -> Tuple[float, float, float]:
        """根据key获取颜色"""
        if key not in self._color_map:
            hue = (self._color_idx * 0.618033988749895) % 1.0
            self._color_map[key] = colorsys.hsv_to_rgb(hue, 0.6, 0.8)
            self._color_idx += 1
        return self._color_map[key]

    def visualize_board(self, board: CuttingBoard, save_path: Optional[str] = None,
                        dpi: int = 150) -> str:
        """可视化单块原片的排样方案"""
        fig, ax = plt.subplots(1, 1, figsize=(14, 8))

        # 绘制原片轮廓
        plate_rect = patches.Rectangle(
            (0, 0), board.plate_length, board.plate_width,
            linewidth=2, edgecolor='black', facecolor='#f5f5f5'
        )
        ax.add_patch(plate_rect)

        # 绘制每个产品项
        for item in board.placed_items:
            color = self._get_color(item.material)
            rect = patches.Rectangle(
                (item.x, item.y), item.length, item.width,
                linewidth=0.5, edgecolor='gray', facecolor=color, alpha=0.85
            )
            ax.add_patch(rect)

            # 标注（仅当空间足够时）
            min_dim = min(item.length, item.width)
            if min_dim > 30:
                font_size = max(4, min(7, min_dim / 10))
                ax.text(item.x + item.length/2, item.y + item.width/2,
                       f"#{item.item_id}", ha='center', va='center',
                       fontsize=font_size, color='black', fontweight='bold')

        ax.set_xlim(-20, board.plate_length + 20)
        ax.set_ylim(-20, board.plate_width + 20)
        ax.set_aspect('equal')
        ax.set_xlabel('X (mm)', fontsize=10)
        ax.set_ylabel('Y (mm)', fontsize=10)
        ax.set_title(f"原片 #{board.board_id+1} | 材质: {board.material} | "
                     f"利用率: {board.utilization:.1%} | 项数: {len(board.placed_items)}",
                     fontsize=11)

        info_text = (f"原片: {board.plate_length:.0f}×{board.plate_width:.0f} mm\n"
                     f"已用面积: {board.used_area:.0f} mm²\n"
                     f"利用率: {board.utilization:.1%}")
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=8,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        plt.tight_layout()
        if save_path is None:
            save_path = os.path.join(self.output_dir, f"board_{board.board_id + 1}.png")
        plt.savefig(save_path, dpi=dpi, bbox_inches='tight')
        plt.close(fig)
        return save_path

    def visualize_all(self, boards: List[CuttingBoard], max_boards: Optional[int] = None,
                      dpi: int = 150) -> List[str]:
        """可视化所有原片"""
        paths = []
        n = len(boards) if max_boards is None else min(len(boards), max_boards)
        print(f"[信息] 正在生成 {n} 张排样图...")
        for i in range(n):
            path = self.visualize_board(boards[i], dpi=dpi)
            paths.append(path)
            if (i + 1) % 10 == 0:
                print(f"  已完成 {i+1}/{n}")
        print(f"[信息] 排样图保存至: {self.output_dir}/")
        return paths


# ============================================================
# 第五部分：结果输出
# ============================================================

def generate_cut_program(boards: List[CuttingBoard], output_path: str = "cut_program.csv"):
    """生成排样方案CSV文件"""
    rows = []
    for board in boards:
        for item in board.placed_items:
            rows.append({
                '原片材质': board.material,
                '原片序号': board.board_id,
                '产品id': item.item_id,
                '产品x坐标': round(item.x, 1),
                '产品y坐标': round(item.y, 1),
                '产品x方向长度': round(item.length, 1),
                '产品y方向长度': round(item.width, 1)
            })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"[信息] 排样方案已保存: {output_path} ({len(rows)}条记录)")
    return df


def generate_sum_order(batches_boards: List[List[CuttingBoard]],
                       output_path: str = "sum_order.csv"):
    """生成组批方案CSV文件"""
    rows = []
    for batch_idx, boards in enumerate(batches_boards):
        for board in boards:
            for item in board.placed_items:
                rows.append({
                    '批次序号': batch_idx,
                    '原片材质': board.material,
                    '原片序号': board.board_id,
                    '产品id': item.item_id,
                    '产品x坐标': round(item.x, 1),
                    '产品y坐标': round(item.y, 1),
                    '产品x方向长度': round(item.length, 1),
                    '产品y方向长度': round(item.width, 1)
                })
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"[信息] 组批方案已保存: {output_path} ({len(rows)}条记录)")
    return df


# ============================================================
# 第六部分：主求解流程
# ============================================================

def solve_subproblem1(data_dir: str, params: ProblemParams, output_dir: str = "output_sub1"):
    """求解子问题1：排样优化问题（数据集A）"""
    print("\n" + "="*60)
    print("子问题1：排样优化问题（数据集A）")
    print("="*60)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "output_images"), exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(data_dir, "dataA*.csv")))
    if not csv_files:
        print(f"[错误] 未找到数据文件: {data_dir}/dataA*.csv")
        return

    packer = EnhancedGuillotinePacker(
        plate_length=params.plate_length,
        plate_width=params.plate_width,
        allow_rotation=params.allow_rotation
    )

    visualizer = CuttingVisualizer(output_dir=os.path.join(output_dir, "output_images"))

    grand_used_area = 0
    grand_total_boards = 0
    grand_total_items = 0

    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        print(f"\n--- 处理 {filename} ---")

        try:
            df = load_items_from_csv(csv_file)
        except Exception as e:
            print(f"[错误] 读取失败: {e}")
            continue

        if len(df) == 0:
            print("[警告] 文件为空，跳过")
            continue

        materials = df['item_material'].unique()
        print(f"  产品项数: {len(df)}, 材质数: {len(materials)}")

        # 子问题1：排样优化，不考虑材质约束，所有项一起排样
        # （子问题1为"单材质"场景，将所有项视为同一材质）
        all_boards = packer.pack(df, material="mixed" if len(materials) > 1 else materials[0])

        n_boards = len(all_boards)
        n_items = sum(len(b.placed_items) for b in all_boards)
        total_area = sum(b.total_area for b in all_boards)
        used_area = sum(b.used_area for b in all_boards)
        util = used_area / total_area if total_area > 0 else 0

        print(f"  使用原片数: {n_boards}")
        print(f"  排布产品项数: {n_items}")
        print(f"  板材利用率: {util:.2%}")

        grand_total_boards += n_boards
        grand_total_items += n_items
        grand_used_area += used_area

        visualizer.visualize_all(all_boards, max_boards=20)
        generate_cut_program(all_boards, os.path.join(output_dir, f"cut_program_{filename}"))

    grand_plate_area = grand_total_boards * params.plate_length * params.plate_width
    grand_util = grand_used_area / grand_plate_area if grand_plate_area > 0 else 0
    print(f"\n{'='*60}")
    print(f"子问题1总体结果:")
    print(f"  总原片数: {grand_total_boards}")
    print(f"  总产品项数: {grand_total_items}")
    print(f"  总体利用率: {grand_util:.2%}")
    print(f"{'='*60}")


def solve_subproblem2(data_dir: str, params: ProblemParams, output_dir: str = "output_sub2"):
    """求解子问题2：订单组批+排样优化问题（数据集B）"""
    print("\n" + "="*60)
    print("子问题2：订单组批+排样优化问题（数据集B）")
    print("="*60)

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "output_images"), exist_ok=True)

    csv_files = sorted(glob.glob(os.path.join(data_dir, "dataB*.csv")))
    if not csv_files:
        print(f"[错误] 未找到数据文件: {data_dir}/dataB*.csv")
        return

    packer = EnhancedGuillotinePacker(
        plate_length=params.plate_length,
        plate_width=params.plate_width,
        allow_rotation=params.allow_rotation
    )

    batcher = OrderBatcher(
        max_item_num=params.max_item_num,
        max_item_area=params.max_item_area,
        plate_length=params.plate_length,
        plate_width=params.plate_width
    )

    visualizer = CuttingVisualizer(output_dir=os.path.join(output_dir, "output_images"))

    grand_total_boards = 0
    grand_total_items = 0
    grand_total_used_area = 0

    for csv_file in csv_files:
        filename = os.path.basename(csv_file)
        print(f"\n--- 处理 {filename} ---")

        try:
            df = load_items_from_csv(csv_file)
        except Exception as e:
            print(f"[错误] 读取失败: {e}")
            continue

        if len(df) == 0:
            print("[警告] 文件为空，跳过")
            continue

        print(f"  总产品项数: {len(df)}")
        print(f"  材质种类: {df['item_material'].nunique()}")
        print(f"  订单数量: {df['item_order'].nunique()}")

        # 步骤1：订单组批
        print("  正在组批...")
        batches = batcher.batch_orders(df)
        print(f"  生成批次数: {len(batches)}")

        # 步骤2：对每个批次进行排样
        all_batch_boards = []
        for batch_idx, batch_df in enumerate(batches):
            materials = batch_df['item_material'].unique()
            batch_boards = []

            for mat in materials:
                mat_df = batch_df[batch_df['item_material'] == mat]
                boards = packer.pack(mat_df, material=mat)
                batch_boards.extend(boards)

            all_batch_boards.append(batch_boards)

            if (batch_idx + 1) % 20 == 0:
                print(f"    已处理 {batch_idx+1}/{len(batches)} 个批次")

        # 步骤3：统计结果
        n_boards = sum(len(boards) for boards in all_batch_boards)
        n_items = sum(sum(len(b.placed_items) for b in boards) for boards in all_batch_boards)
        total_area = n_boards * params.plate_length * params.plate_width
        used_area = sum(sum(b.used_area for b in boards) for boards in all_batch_boards)
        util = used_area / total_area if total_area > 0 else 0

        print(f"  使用原片数: {n_boards}")
        print(f"  排布产品项数: {n_items}")
        print(f"  板材利用率: {util:.2%}")

        grand_total_boards += n_boards
        grand_total_items += n_items
        grand_total_used_area += used_area

        # 可视化（每个文件最多10块）
        all_boards_flat = [b for boards in all_batch_boards for b in boards]
        visualizer.visualize_all(all_boards_flat, max_boards=10)

        # 生成组批方案CSV
        generate_sum_order(all_batch_boards,
                          os.path.join(output_dir, f"sum_order_{filename}"))

    grand_plate_area = grand_total_boards * params.plate_length * params.plate_width
    grand_util = grand_total_used_area / grand_plate_area if grand_plate_area > 0 else 0
    print(f"\n{'='*60}")
    print(f"子问题2总体结果:")
    print(f"  总原片数: {grand_total_boards}")
    print(f"  总产品项数: {grand_total_items}")
    print(f"  总体利用率: {grand_util:.2%}")
    print(f"{'='*60}")


# ============================================================
# 第七部分：主入口
# ============================================================

def main():
    """主函数"""
    print("="*60)
    print("方形件组批优化问题 — 2D板材切割下料求解器")
    print("="*60)

    work_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(work_dir)

    # 从Word文档提取参数
    docx_files = glob.glob("*.docx")
    params = ProblemParams()

    if docx_files:
        print(f"\n[步骤1] 从文档提取参数: {docx_files[0]}")
        params = extract_params_from_docx(docx_files[0])
    else:
        print("\n[步骤1] 未找到Word文档，使用默认参数")
        print(f"  原片: {params.plate_length}x{params.plate_width}mm, "
              f"批次上限: {params.max_item_num}项/{params.max_item_area}m²")

    # 求解子问题1
    sub1_dir = os.path.join(work_dir, "子问题1-数据集A")
    if os.path.exists(sub1_dir):
        solve_subproblem1(sub1_dir, params)
    else:
        print(f"\n[警告] 子问题1数据目录不存在: {sub1_dir}")

    # 求解子问题2
    sub2_dir = os.path.join(work_dir, "子问题2-数据集B")
    if os.path.exists(sub2_dir):
        solve_subproblem2(sub2_dir, params)
    else:
        print(f"\n[警告] 子问题2数据目录不存在: {sub2_dir}")

    print("\n" + "="*60)
    print("求解完成！")
    print("="*60)


if __name__ == "__main__":
    main()