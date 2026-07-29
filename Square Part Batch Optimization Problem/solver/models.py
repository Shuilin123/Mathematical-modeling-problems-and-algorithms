#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模型
========
定义排样过程中的核心数据结构。
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PlacedItem:
    """已放置的产品项"""
    item_id: int          # 产品ID
    material: str         # 材质
    x: float              # 左下角x坐标 (mm)
    y: float              # 左下角y坐标 (mm)
    length: float         # x方向长度 (mm)
    width: float          # y方向长度 (mm)
    rotated: bool = False # 是否旋转
    order: str = ""       # 订单号


@dataclass
class CuttingBoard:
    """一块原片的排样结果"""
    board_id: int         # 原片序号
    material: str         # 材质
    plate_length: float   # 原片长度 (mm)
    plate_width: float    # 原片宽度 (mm)
    placed_items: List[PlacedItem] = field(default_factory=list)

    @property
    def used_area(self):
        """已使用面积"""
        return sum(it.length * it.width for it in self.placed_items)

    @property
    def total_area(self):
        """原片总面积"""
        return self.plate_length * self.plate_width

    @property
    def utilization(self):
        """利用率"""
        return self.used_area / self.total_area if self.total_area > 0 else 0