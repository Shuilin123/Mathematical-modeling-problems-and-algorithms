#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
订单组批模块
============
按约束条件将订单分组为批次。

约束条件：
1. 每份订单当且仅当出现在一个批次中
2. 每个批次中相同材质的产品项才能使用同一块原片
3. 每个批次产品项总数不超过max_item_num
4. 每个批次产品项面积总和不超过max_item_area
"""

from collections import defaultdict
from typing import List

import pandas as pd


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
        """
        对产品项数据进行组批，返回批次列表

        Args:
            df: 包含产品项数据的DataFrame

        Returns:
            批次列表，每个批次是一个DataFrame
        """
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