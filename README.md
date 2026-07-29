# 数学建模与算法

这一些数学建模问题部分解决方案 [持续更新]

## 一、高温作业专用服装设计

皮肤外层温度变化曲线

### 1、温度分布

![problem1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2018/A/problem1.png)

### 2、皮肤侧温度变化曲线

![problem1\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2018/A/problem1\_1.png)

### 3、热传递仿真

![griaph](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2018/A/griaph.gif)

4、满足条件的皮肤侧温度变化曲线

![problem2\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2018/A/problem2\_1.png)

## 二、多波束测线问题
### 数学模型
![problem2\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2023/B/fig/MCM-2023%20(1).jpg)
![problem2\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2023/B/fig/MCM-2023%20(2).jpg)
![problem2\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2023/B/fig/MCM-2023%20(3).jpg)
![problem2\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/MCM/2023/B/fig/MCM-2023%20(4).jpg)

## 三、方形件组批优化

### 问题1 排样优化问题
  
  在满足生产订单需求和相关约束条件下的结果。
  约束：
  - i.在相同栈（stack）里的产品项（item）的宽度（或长度）应该相同；
  - ii.最终切割生成的产品项是完整的，非拼接而成。
最后求解混合整数规划得到材料切割结果，样例如下:
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub1/output_images/A_Board%20(1).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub1/output_images/A_Board%20(2).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub1/output_images/A_Board%20(3).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub1/output_images/A_Board%20(4).png)

### 问题2 订单组批问题

   通过混合整数规划模型，对数据集B中全部的订单进行组批，然后对每个批次进行独立排样，在满足订单需求和相关约束条件下，使得板材原片的用量尽可能少。
在满足子问题1约束的基础上进一步要求：
- i 每份订单当且仅当出现在一个批次中；
- ii 每个批次中的相同材质的产品项（item）才能使用同一块板材原片进行排样；
- iii 为保证加工环节快速流转，每个批次产品项（item）总数不能超过限定值；
- iv 因工厂产能限制，每个批次产品项（item）的面积总和不能超过限定值；
得到同一材料切割结果，样例如下:
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub2/output_images/B_board%20(1).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub2/output_images/B_board%20(2).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub2/output_images/B_board%20(3).png)
![problem3\_1](https://github.com/Shuilin123/Mathematical-modeling-problems-and-algorithms/blob/master/Square%20Part%20Batch%20Optimization%20Problem/output_sub2/output_images/B_board%20(4).png)


