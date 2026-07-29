#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
结果输出模块
============
生成排样方案和组批方案的CSV文件。
"""

from typing import List

import pandas as pd

from solver.models import CuttingBoard


def generate_cut_program(boards: List[CuttingBoard], output_path: str = "cut_program.csv"):
    """
    生成排样方案CSV文件

    Args:
        boards: 排样结果列表
        output_path: 输出CSV路径

    Returns:
        生成的DataFrame
    """
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
    """
    生成组批方案CSV文件

    Args:
        batches_boards: 各批次的排样结果列表
        output_path: 输出CSV路径

    Returns:
        生成的DataFrame
    """
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