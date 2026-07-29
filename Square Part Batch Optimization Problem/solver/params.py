#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
问题参数定义
============
定义方形件组批优化问题的所有参数。
"""

from dataclasses import dataclass


@dataclass
class ProblemParams:
    """问题参数数据类"""
    plate_length: float = 2440.0     # 原片长度 (mm)
    plate_width: float = 1220.0      # 原片宽度 (mm)
    max_item_num: int = 1000         # 每批次最大产品项数
    max_item_area: float = 250.0     # 每批次最大产品项面积 (m²)
    allow_rotation: bool = True      # 是否允许旋转
    guillotine_cut: bool = True      # 是否齐头切
    max_stages: int = 3              # 最大切割阶段数