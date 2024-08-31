clc,clear,close all
% 导入基底刺激值和目标颜料刺激值
load('Lab.mat');%样本的Lab
load('poly_coef.mat');%多项式系数
load('XYZ_Base.mat');
% 用什么来配颜料？
% 计算当前配方下的R
clc,clear,close all
load('Lab.mat');%样本的Lab
load('poly_coef.mat');%多项式系数
load('XYZ_Base.mat');
num=3;
m=1;%kg
x0=[0,0,0];
Solution=[];ObjectiveValue=[];
options = optimoptions('ga','ConstraintTolerance',1e-6,'PlotFcn', @gaplotbestf);
for i=1:10
    L0=L(i);
    a0=a(i);
    b0=b(i);
    % 将固定参数传递给 objfun
    objfun = @(optimInput)obj_fun(optimInput,poly_Coefficients_r,...
        poly_Coefficients_y,poly_Coefficients_b,K_S0,data,X0,Y0,Z0,L0,a0,b0);
    
    % 求解
    Aeq=[1,1,1];
    beq=[m];
    [solution,objectiveValue] = ga(objfun,num,[],[],Aeq,beq,zeros(num,1),m*ones(num,...
        1),[],options);
    Solution=[Solution;solution];
    ObjectiveValue=[ObjectiveValue,objectiveValue];
    % 清除变量
    clearvars objfun
end
name={'样品色号','红色','蓝色','黄色','色差'};
index=1:10;
Table=table(index',Solution(:,1)/m,Solution(:,2)/m,Solution(:,3)/m,ObjectiveValue','VariableNames',name);
writetable(Table,'problem2_ans.xlsx');
