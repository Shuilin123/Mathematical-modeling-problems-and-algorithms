#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
排样算法模块
============
3阶段齐头切排样器，采用Shelf-Based FFD算法。

核心算法：
  - 第1阶段（Stripe/条带）：原片沿y方向切为若干水平条带
  - 第2阶段（Stack/栈）：每条带沿x方向切为若干垂直栈
  - 第3阶段（Item/产品项）：每栈沿x方向排列产品项（同宽度归并）

约束：同一栈内产品项的y方向尺寸（宽度）必须相同。
"""

import random
from typing import List

import pandas as pd

from solver.models import PlacedItem, CuttingBoard


class GuillotineCutPacker:
    """
    3阶段齐头切排样器（基础版）

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
                prefer_a = (l >= w)  # l>=w时, 朝向A的ew=w(短边)
            elif strategy == 'length_first':
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
        stacks = self._build_stacks(oriented, tol_pct, tol_min)
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
        items_sorted = sorted(items, key=lambda x: x['ew'])

        # 贪心聚类：将相邻宽度的项归入同一组
        clusters = []  # [{'items': [...], 'cluster_w': 最大宽度}]
        for item in items_sorted:
            ew = item['ew']
            placed = False
            for cluster in clusters:
                cluster_w = cluster['cluster_w']
                tol = max(cluster_w * width_tolerance_pct, width_tolerance_min)
                if ew <= cluster_w + tol:
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

        boards_data = []  # [{'stripes': [...], 'used_y': y}]

        for sinfo in stacks_sorted:
            sw, sl = sinfo['stack_w'], sinfo['stack_l']

            best_board_idx = -1
            best_stripe_idx = -1
            best_is_new_stripe = False
            best_score = float('inf')

            for bidx, bdata in enumerate(boards_data):
                # 尝试放入已有条带
                for sidx, stripe in enumerate(bdata['stripes']):
                    stripe_h = stripe['height']
                    if sw <= stripe_h and stripe['used_l'] + sl <= self.L:
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
                    remaining_w = self.W - bdata['used_y'] - sw
                    score = remaining_w * self.L * 0.1
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
        oriented_sorted = sorted(oriented, key=lambda x: -(x['el'] * x['ew']))

        boards = []
        board_id = 0

        shelves = []  # [{'height': h, 'items': [...], 'used_l': used_length}]
        current_y = 0

        for item in oriented_sorted:
            el, ew = item['el'], item['ew']
            placed = False

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

    def _pack_shelf_length_desc(self, items: List[dict], material: str) -> List[CuttingBoard]:
        """
        按长边降序的Shelf排样算法

        优先放置长边较大的项，有利于填满条带长度
        """
        oriented = self._orient_items(items, 'width_first')
        oriented_sorted = sorted(oriented, key=lambda x: -x['el'])

        boards = []
        board_id = 0

        shelves = []
        current_y = 0

        for item in oriented_sorted:
            el, ew = item['el'], item['ew']
            placed = False

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

            board_utils = []
            for i, board in enumerate(boards):
                used_area = sum(it.length * it.width for it in board.placed_items)
                util = used_area / plate_area
                board_utils.append((i, util, used_area))

            board_utils.sort(key=lambda x: x[1])

            for src_idx, src_util, src_area in board_utils:
                if src_util > 0.85:
                    continue

                src_board = boards[src_idx]

                items_to_place = []
                for it in src_board.placed_items:
                    items_to_place.append({
                        'item_id': it.item_id, 'material': it.material,
                        'length': it.length, 'width': it.width,
                        'el': it.length, 'ew': it.width,
                        'rotated': it.rotated, 'order': it.order,
                        'item_num': 1, 'area': it.length * it.width
                    })

                placed_items = []
                remaining_items = list(items_to_place)

                for dst_idx, dst_board in enumerate(boards):
                    if dst_idx == src_idx:
                        continue
                    if not remaining_items:
                        break

                    used_y = max((it.y + it.width) for it in dst_board.placed_items) if dst_board.placed_items else 0
                    remaining_y = self.W - used_y

                    if remaining_y < 10:
                        continue

                    still_remaining = []
                    for item in remaining_items:
                        if item['ew'] <= remaining_y and item['el'] <= self.L:
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

                if not remaining_items:
                    boards.pop(src_idx)
                    improved = True
                    break

        for i, board in enumerate(boards):
            board.board_id = i

        return boards