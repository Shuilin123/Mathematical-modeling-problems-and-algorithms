#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化模块
==========
切割排布结果的可视化。
"""

import os
import colorsys
from typing import List, Tuple, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from solver.models import CuttingBoard


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
        """
        可视化单块原片的排样方案

        Args:
            board: 排样结果
            save_path: 保存路径（默认自动生成）
            dpi: 图片分辨率

        Returns:
            保存的图片路径
        """
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
        """
        可视化所有原片

        Args:
            boards: 排样结果列表
            max_boards: 最多可视化原片数（None表示全部）
            dpi: 图片分辨率

        Returns:
            保存的图片路径列表
        """
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