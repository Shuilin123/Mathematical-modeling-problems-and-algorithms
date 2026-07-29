#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据加载模块
============
从CSV文件加载产品项数据。
"""

import os
import pandas as pd


def load_items_from_csv(csv_path: str) -> pd.DataFrame:
    """
    从CSV文件加载产品项数据

    必要列: item_id, item_material, item_num, item_length, item_width, item_order

    Args:
        csv_path: CSV文件路径

    Returns:
        包含产品项数据的DataFrame，额外添加area列

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 缺少必要列
    """
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