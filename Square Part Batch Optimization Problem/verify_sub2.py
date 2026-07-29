"""验证子问题2输出CSV坐标正确性"""
import pandas as pd
L, W = 2440, 1220

print('=== 子问题2坐标验证 ===')
for i in range(1, 6):
    df = pd.read_csv(f'output_sub2/sum_order_dataB{i}.csv')
    x_col, y_col = '产品x坐标', '产品y坐标'
    xl_col, yl_col = '产品x方向长度', '产品y方向长度'
    
    overflow_x = (df[x_col] + df[xl_col] > L + 0.1).sum()
    overflow_y = (df[y_col] + df[yl_col] > W + 0.1).sum()
    max_x = (df[x_col] + df[xl_col]).max()
    max_y = (df[y_col] + df[yl_col]).max()
    print(f'dataB{i}: {len(df)}项, x越界={overflow_x}, y越界={overflow_y}, max_x={max_x:.0f}, max_y={max_y:.0f}')
    
    # 按(批次序号, 原片材质, 原片序号)分组检查重叠
    # 原片序号只在同一材质内唯一
    groups = list(df.groupby(['批次序号', '原片材质', '原片序号']))
    sample_groups = groups[::max(1, len(groups)//100)]
    overlap_count = 0
    checked = 0
    for (batch_id, mat, board_id), bdf in sample_groups:
        items = list(zip(bdf[x_col], bdf[y_col], bdf[xl_col], bdf[yl_col]))
        for j in range(len(items)):
            x1,y1,l1,w1 = items[j]
            for k in range(j+1, len(items)):
                x2,y2,l2,w2 = items[k]
                if (x1 < x2+l2 and x1+l1 > x2 and y1 < y2+w2 and y1+w1 > y2):
                    overlap_count += 1
        checked += 1
    if overlap_count > 0:
        print(f'  警告: 抽样{checked}块中有 {overlap_count} 对重叠项!')
    else:
        print(f'  抽样{checked}块原片: 0重叠')

print('\n=== 子问题1坐标验证 ===')
for i in range(1, 6):
    df = pd.read_csv(f'output_sub1/cut_program_dataA{i}.csv')
    x_col, y_col = '产品x坐标', '产品y坐标'
    xl_col, yl_col = '产品x方向长度', '产品y方向长度'
    
    overflow_x = (df[x_col] + df[xl_col] > L + 0.1).sum()
    overflow_y = (df[y_col] + df[yl_col] > W + 0.1).sum()
    max_x = (df[x_col] + df[xl_col]).max()
    max_y = (df[y_col] + df[yl_col]).max()
    print(f'dataA{i}: {len(df)}项, x越界={overflow_x}, y越界={overflow_y}, max_x={max_x:.0f}, max_y={max_y:.0f}')