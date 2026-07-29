# 方形件组批优化问题

## 一、问题概述

本问题包含两个子问题：

- **子问题1（排样优化）**：给定同一材质的方形件集合，在满足"齐头切"（Guillotine cut）约束和3阶段精确排样约束下，最小化使用的原片数量。
- **子问题2（订单组批+排样优化）**：对多材质、多订单的方形件集合进行组批，每个批次内相同材质的件才能共用同一原片，同时满足批次容量约束。

---

## 二、符号说明

### 2.1 集合与索引

| 符号 | 说明 |
|------|------|
| $I$ | 产品项（item）集合，索引 $i \in I$ |
| $J$ | 批次集合，索引 $j \in J$ |
| $M$ | 材质集合，索引 $m \in M$ |
| $O$ | 订单集合，索引 $o \in O$ |
| $I_o$ | 属于订单 $o$ 的产品项子集 |
| $I_m$ | 材质为 $m$ 的产品项子集 |
| $K$ | 原片集合，索引 $k \in K$ |

### 2.2 参数

| 符号 | 说明 |
|------|------|
| $L$ | 原片长度，$L = 2440$ mm |
| $W$ | 原片宽度，$W = 1220$ mm |
| $l_i$ | 产品项 $i$ 的长度（mm） |
| $w_i$ | 产品项 $i$ 的宽度（mm） |
| $n_i$ | 产品项 $i$ 的需求数量 |
| $N_{\max}$ | 单批次产品项数上限，$N_{\max} = 1000$ |
| $A_{\max}$ | 单批次面积上限，$A_{\max} = 250$ m² |
| $a_i$ | 产品项 $i$ 的面积，$a_i = l_i \times w_i$ |

### 2.3 决策变量

| 符号 | 类型 | 说明 |
|------|------|------|
| $x_{ij}$ | 0-1变量 | 产品项 $i$ 是否分配到批次 $j$ |
| $y_{jk}$ | 0-1变量 | 批次 $j$ 是否使用原片 $k$ |
| $z_{ik}$ | 0-1变量 | 产品项 $i$ 是否排布在原片 $k$ 上 |
| $p_{ik}^x$ | 连续变量 | 产品项 $i$ 在原片 $k$ 上的x坐标（左下角） |
| $p_{ik}^y$ | 连续变量 | 产品项 $i$ 在原片 $k$ 上的y坐标（左下角） |
| $o_i$ | 0-1变量 | 产品项 $i$ 是否旋转90°（长宽互换） |
| $u_k$ | 0-1变量 | 原片 $k$ 是否被使用 |

---

## 三、子问题1：排样优化模型

### 3.1 约束条件

#### 约束(1)：目标函数

最小化使用的原片总数。

$$\min \sum_{k \in K} u_k$$

#### 约束(2)：需求满足约束

每个产品项必须被完整排布到原片上，需求量 $n_i$ 必须全部满足。

$$\sum_{k \in K} z_{ik} = n_i, \quad \forall i \in I$$

#### 约束(3)-(4)：旋转定义

$l_i'$ 和 $w_i'$ 为考虑旋转后的有效长宽。当 $o_i = 0$ 时不旋转，$o_i = 1$ 时旋转90°（长宽互换）。

$$l_i' = l_i(1-o_i) + w_i \cdot o_i, \quad \forall i \in I$$

$$w_i' = w_i(1-o_i) + l_i \cdot o_i, \quad \forall i \in I$$

#### 约束(5)-(6)：原片边界约束

产品项不能超出原片边界。采用大M法：当产品项 $i$ 排布在原片 $k$ 上（$z_{ik} = 1$）时，约束退化为 $p_{ik}^x + l_i' \leq L$ 和 $p_{ik}^y + w_i' \leq W$；否则通过大M放宽。

$$p_{ik}^x + l_i' \leq L + M(1 - z_{ik}), \quad \forall i \in I, k \in K$$

$$p_{ik}^y + w_i' \leq W + M(1 - z_{ik}), \quad \forall i \in I, k \in K$$

#### 约束(7)-(11)：不重叠约束

对于同一原片 $k$ 上的任意两个产品项 $i_1, i_2$，至少满足以下四个方向之一的不重叠条件：

$$p_{i_1k}^x + l_{i_1}' \leq p_{i_2k}^x \;\lor\; p_{i_2k}^x + l_{i_2}' \leq p_{i_1k}^x \;\lor\; p_{i_1k}^y + w_{i_1}' \leq p_{i_2k}^y \;\lor\; p_{i_2k}^y + w_{i_2}' \leq p_{i_1k}^y$$

使用大M法将析取约束线性化，其中 $M$ 为足够大的常数，$\alpha_{i_1i_2k}^r \in \{0,1\}$ 为辅助0-1变量，约束(11)确保至少一个方向的不重叠条件被激活。

$$p_{i_1k}^x + l_{i_1}' \leq p_{i_2k}^x + M(1-\alpha_{i_1i_2k}^1), \quad \forall i_1 < i_2, k \in K$$

$$p_{i_2k}^x + l_{i_2}' \leq p_{i_1k}^x + M(1-\alpha_{i_1i_2k}^2), \quad \forall i_1 < i_2, k \in K$$

$$p_{i_1k}^y + w_{i_1}' \leq p_{i_2k}^y + M(1-\alpha_{i_1i_2k}^3), \quad \forall i_1 < i_2, k \in K$$

$$p_{i_2k}^y + w_{i_2}' \leq p_{i_1k}^y + M(1-\alpha_{i_1i_2k}^4), \quad \forall i_1 < i_2, k \in K$$

$$\alpha_{i_1i_2k}^1 + \alpha_{i_1i_2k}^2 + \alpha_{i_1i_2k}^3 + \alpha_{i_1i_2k}^4 \geq 1, \quad \forall i_1 < i_2, k \in K$$

#### 约束(12)-(14)：齐头切（Guillotine Cut）约束

排样方案必须满足3阶段齐头切约束：

- **第1阶段**：原片沿水平方向切割为若干条带（Stripe），每条带宽度为 $h_s$（$s$ 为条带索引），约束(12)保证条带总宽度不超过原片宽度
- **第2阶段**：每条带沿垂直方向切割为若干栈（Stack），约束(13)保证同一栈内产品项y方向宽度相同
- **第3阶段**：每栈沿水平方向切割为产品项（Item），约束(14)保证同一栈内产品项长度之和不超过原片长度

$$\sum_{s} h_s \leq W, \quad h_s > 0$$

$$w_{i_1}' = w_{i_2}', \quad \forall i_1, i_2 \in \text{Stack}_t$$

$$\sum_{i \in \text{Stack}_t} l_i' \leq L$$

#### 约束(15)：变量关联约束

确保产品项只能排布到已使用的原片上。

$$z_{ik} \leq u_k, \quad \forall i \in I, k \in K$$

#### 约束(16)：坐标非负约束

$$p_{ik}^x \geq 0, \quad p_{ik}^y \geq 0, \quad \forall i \in I, k \in K$$

#### 约束(17)：变量域约束

$$z_{ik}, u_k, o_i \in \{0, 1\}, \quad \alpha_{i_1i_2k}^r \in \{0, 1\}$$

### 3.2 数学规划标准形式

$$\min \sum_{k \in K} u_k \tag{1}$$

s.t.

$$\sum_{k \in K} z_{ik} = n_i, \quad \forall i \in I \tag{2}$$

$$l_i' = l_i(1-o_i) + w_i \cdot o_i, \quad \forall i \in I \tag{3}$$

$$w_i' = w_i(1-o_i) + l_i \cdot o_i, \quad \forall i \in I \tag{4}$$

$$p_{ik}^x + l_i' \leq L + M(1 - z_{ik}), \quad \forall i \in I, k \in K \tag{5}$$

$$p_{ik}^y + w_i' \leq W + M(1 - z_{ik}), \quad \forall i \in I, k \in K \tag{6}$$

$$p_{i_1k}^x + l_{i_1}' \leq p_{i_2k}^x + M(1-\alpha_{i_1i_2k}^1), \quad \forall i_1 < i_2, k \in K \tag{7}$$

$$p_{i_2k}^x + l_{i_2}' \leq p_{i_1k}^x + M(1-\alpha_{i_1i_2k}^2), \quad \forall i_1 < i_2, k \in K \tag{8}$$

$$p_{i_1k}^y + w_{i_1}' \leq p_{i_2k}^y + M(1-\alpha_{i_1i_2k}^3), \quad \forall i_1 < i_2, k \in K \tag{9}$$

$$p_{i_2k}^y + w_{i_2}' \leq p_{i_1k}^y + M(1-\alpha_{i_1i_2k}^4), \quad \forall i_1 < i_2, k \in K \tag{10}$$

$$\alpha_{i_1i_2k}^1 + \alpha_{i_1i_2k}^2 + \alpha_{i_1i_2k}^3 + \alpha_{i_1i_2k}^4 \geq 1, \quad \forall i_1 < i_2, k \in K \tag{11}$$

$$\sum_{s} h_s \leq W, \quad h_s > 0 \tag{12}$$

$$w_{i_1}' = w_{i_2}', \quad \forall i_1, i_2 \in \text{Stack}_t \tag{13}$$

{