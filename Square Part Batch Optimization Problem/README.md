#                                        方形件组批优化问题 

## 项目简介

本项目求解2022年数学建模B题"方形件组批优化问题"，包含两个子问题：

- **子问题1（数据集A）**：给定一批同材质订单，在齐头切约束下排样到原片上，最小化原片用量
- **子问题2（数据集B）**：给定多材质订单，需先按材质分组组批，再对每批排样，最小化原片用量

## 算法概述

### 排样算法（子问题1 & 子问题2共用）

采用 **3-Stage Exact Guillotine Cut** 排样模式（条带→栈→产品项），核心流程：

1. **朝向决策**：对每个产品项尝试0°/90°旋转
2. **宽度聚类**：将相近宽度的产品项归并为同一条带，容差 `max(ew × tol_pct, tol_min)`
3. **全局最优适配**：遍历所有原片的所有条带位置，选择浪费最小的放置
4. **Shelf变体**：Bottom-Left 和 Next-Fit 两种策略
5. **随机扰动**：对排序进行20次随机扰动，避免局部最优
6. **后处理合并**：将利用率过低的稀疏原片合并

**54种方案比较选优**：5种排序策略 × 4容差 × 3朝向 × 2 Shelf算法 + 20次随机扰动

### 组批算法（子问题2专用）

1. 按材质分组
2. 每组内按面积降序排列
3. 贪心装批：依次放入当前未满批次，装满则开新批
4. 对每批独立调用排样算法

## 使用方法

### 环境要求

- Python 3.8+
- 依赖：`pandas`, `numpy`, `matplotlib`

### 运行子问题1

```bash
python run_sub1.py
```

输出文件：`output_sub1/cut_program_dataA1.csv` ~ `cut_program_dataA5.csv`

### 运行子问题2

```bash
python run_sub2.py
```

输出文件：`output_sub2/sum_order_dataB1.csv` ~ `sum_order_dataB5.csv`

### 验证输出

```bash
python verify_output.py   # 验证子问题1：越界检查 + 重叠检查
python verify_sub2.py     # 验证子问题2：越界检查 + 重叠检查（按批次+材质+序号分组）
```

## 实验结果

### 子问题1（数据集A）

| 数据集 | 原片数量 | 利用率 |
|--------|---------|--------|
| dataA1 | 93      | 90.01% |
| dataA2 | 93      | 89.17% |
| dataA3 | 93      | 90.15% |
| dataA4 | 92      | 89.25% |
| dataA5 | 93      | 90.18% |
| **总计** | **464** | **89.75%** |

### 子问题2（数据集B）

| 数据集 | 原片数量 | 利用率 |
|--------|---------|--------|
| dataB1 | 18,326  | 74.42% |
| dataB2 | 12,312  | 72.11% |
| dataB3 | 11,999  | 73.02% |
| dataB4 | 12,790  | 74.22% |
| dataB5 | 19,998  | 70.17% |
| **总计** | **75,425** | **72.66%** |

## 项目结构

```
├── cutting_stock_solver.py    # 向后兼容的薄包装，重新导出 solver 包接口
├── run_sub1.py                # 子问题1运行入口
├── run_sub2.py                # 子问题2运行入口
├── verify_output.py           # 子问题1输出验证
├── verify_sub2.py             # 子问题2输出验证
├── model_document.md          # 数学建模文档
│
├── solver/                    # 核心求解器包
│   ├── __init__.py            # 包入口，统一导出公共接口
│   ├── params.py              # 问题参数定义（ProblemParams）
│   ├── data_loader.py         # CSV数据加载（load_items_from_csv）
│   ├── models.py              # 数据模型（PlacedItem, CuttingBoard）
│   ├── packer.py              # 排样算法（GuillotineCutPacker, EnhancedGuillotinePacker）
│   ├── batcher.py             # 订单组批（OrderBatcher）
│   ├── visualizer.py          # 切割排布可视化（CuttingVisualizer）
│   ├── output.py              # 结果CSV输出（generate_cut_program, generate_sum_order）
│   └── solver.py              # 主求解流程（solve_subproblem1, solve_subproblem2, main）
│
├── 子问题1-数据集A/            # 输入数据（5个CSV）
├── 子问题2-数据集B/            # 输入数据（5个CSV）
│
├── output_sub1/               # 子问题1输出
│   ├── cut_program_dataA*.csv
│   └── output_images/         # 排样可视化图
│
└── output_sub2/               # 子问题2输出
    ├── sum_order_dataB*.csv
    └── output_images/         # 排样可视化图
```

### 模块职责说明

| 模块 | 职责 | 核心类/函数 |
|------|------|------------|
| `solver/params.py` | 问题参数定义 | `ProblemParams` |
| `solver/data_loader.py` | CSV数据加载与校验 | `load_items_from_csv()` |
| `solver/models.py` | 排样数据模型 | `PlacedItem`, `CuttingBoard` |
| `solver/packer.py` | 3阶段齐头切排样算法 | `GuillotineCutPacker`, `EnhancedGuillotinePacker` |
| `solver/batcher.py` | 订单组批（贪心策略） | `OrderBatcher` |
| `solver/visualizer.py` | 排样结果可视化 | `CuttingVisualizer` |
| `solver/output.py` | CSV结果输出 | `generate_cut_program()`, `generate_sum_order()` |
| `solver/solver.py` | 子问题求解主流程 | `solve_subproblem1()`, `solve_subproblem2()`, `main()` |

## 输出格式

- **子问题1**：`cut_program_dataA*.csv` — 每行为一个产品项在原片上的排样位置
- **子问题2**：`sum_order_dataB*.csv` — 含批次序号、原片材质、原片序号、产品项坐标等信息

详细列说明见 [`model_document.md`](model_document.md) 第十章。
