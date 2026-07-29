#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主求解流程
==========
子问题1（排样优化）和子问题2（订单组批+排样优化）的完整求解流程。
"""

import os
import glob

from solver.params import ProblemParams
from solver.data_loader import load_items_from_csv
from solver.packer import EnhancedGuillotinePacker
from solver.batcher import OrderBatcher
from solver.visualizer import CuttingVisualizer
from solver.output import generate_cut_program, generate_sum_order


def solve_subproblem1(data_dir: str, params: ProblemParams, output_dir: str = "output_sub1"):
    """
    求解子问题1：排样优化问题（数据集A）

    Args:
        data_dir: 数据目录路径
        params: 问题参数
        output_dir: 输出目录路径
    """
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
    """
    求解子问题2：订单组批+排样优化问题（数据集B）

    Args:
        data_dir: 数据目录路径
        params: 问题参数
        output_dir: 输出目录路径
    """
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


def main():
    """主函数"""
    print("="*60)
    print("方形件组批优化问题 — 2D板材切割下料求解器")
    print("="*60)

    work_dir = os.path.dirname(os.path.abspath(__file__))
    # 当作为solver.solver.main()调用时，work_dir是solver目录，需要回到项目根目录
    if os.path.basename(work_dir) == 'solver':
        work_dir = os.path.dirname(work_dir)
    os.chdir(work_dir)

    # 使用默认参数（不再从Word文档提取）
    params = ProblemParams()
    print(f"\n[参数] 原片: {params.plate_length}x{params.plate_width}mm, "
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