"""运行子问题2完整流程"""
import cutting_stock_solver as cs
import os

work_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(work_dir)

# 提取参数
docx_files = [f for f in os.listdir('.') if f.endswith('.docx') and not f.startswith('~')]
params = cs.ProblemParams()
if docx_files:
    print(f"从文档提取参数: {docx_files[0]}")
    params = cs.extract_params_from_docx(docx_files[0])
else:
    print("使用默认参数")

print(f"原片: {params.plate_length}x{params.plate_width}mm")
print(f"旋转: {params.allow_rotation}, 齐头切: {params.guillotine_cut}")
print(f"批次上限: {params.max_item_num}项/{params.max_item_area}m²")

# 求解子问题2
sub2_dir = os.path.join(work_dir, "子问题2-数据集B")
cs.solve_subproblem2(sub2_dir, params)