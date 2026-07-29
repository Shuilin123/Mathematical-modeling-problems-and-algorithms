#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
方形件组批优化问题 — 2D板材切割下料求解器
===============================================

本文件为向后兼容的薄包装，所有实现已迁移至 solver/ 包。

模块结构：
  solver.params       - 问题参数定义（ProblemParams）
  solver.data_loader  - CSV数据加载（load_items_from_csv）
  solver.models       - 数据模型（PlacedItem, CuttingBoard）
  solver.packer       - 排样算法（GuillotineCutPacker, EnhancedGuillotinePacker）
  solver.batcher      - 订单组批（OrderBatcher）
  solver.visualizer   - 切割排布可视化（CuttingVisualizer）
  solver.output       - 结果CSV输出（generate_cut_program, generate_sum_order）
  solver.solver       - 主求解流程（solve_subproblem1, solve_subproblem2, main）
"""

# 从 solver 包重新导出所有公共接口
from solver import (
    ProblemParams,
    PlacedItem,
    CuttingBoard,
    load_items_from_csv,
    GuillotineCutPacker,
    EnhancedGuillotinePacker,
    OrderBatcher,
    CuttingVisualizer,
    generate_cut_program,
    generate_sum_order,
    solve_subproblem1,
    solve_subproblem2,
    main,
)

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
