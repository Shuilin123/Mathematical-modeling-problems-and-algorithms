#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
方形件组批优化问题 — 2D板材切割下料求解器
===============================================

模块结构：
  - params       : 问题参数定义
  - data_loader  : CSV数据加载
  - models       : 数据模型（PlacedItem, CuttingBoard）
  - packer       : 排样算法（GuillotineCutPacker, EnhancedGuillotinePacker）
  - batcher      : 订单组批（OrderBatcher）
  - visualizer   : 切割排布可视化
  - output       : 结果CSV输出
  - solver       : 主求解流程
"""

from solver.params import ProblemParams
from solver.models import PlacedItem, CuttingBoard
from solver.data_loader import load_items_from_csv
from solver.packer import GuillotineCutPacker, EnhancedGuillotinePacker
from solver.batcher import OrderBatcher
from solver.visualizer import CuttingVisualizer
from solver.output import generate_cut_program, generate_sum_order
from solver.solver import solve_subproblem1, solve_subproblem2, main

__all__ = [
    'ProblemParams',
    'PlacedItem', 'CuttingBoard',
    'load_items_from_csv',
    'GuillotineCutPacker', 'EnhancedGuillotinePacker',
    'OrderBatcher',
    'CuttingVisualizer',
    'generate_cut_program', 'generate_sum_order',
    'solve_subproblem1', 'solve_subproblem2', 'main',
]