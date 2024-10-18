function [x,S0,theta,a,Hw] = solve1(id,L,M,rho,v1,x0,theta0,isplot)
%% solve1 求解问题1
%% 恒定参数
parameters;
%% 问题参数
%id锚链号
%L锚链长度
%M重物球质量 kg
%rho海水密度 kg/m^3
%v1 风速度  m/s
%%导出参数
%1、计算各个部件在海水中的重量 锚链体积忽略不计
w0=chain.w(id)*g-rho*(chain.w(id)/rho_steel)*g;% 锚链单位重量
w1=M*g-rho*(M/(rho_steel))*g;% 重物球重量
%每节钢管在水中的重量
w2=tube.m*g-rho*(tube.m/rho_steel)*g;
%钢桶在海水中的重量
w3=barrel.m*g-rho*(pi*barrel.r*barrel.r*barrel.L)*g;
%2、浮标吃水深度Hw
%浮标所受拉力T为:
T=L*w0+w1+tube.n*w2+w3;
%浮标所受浮力为
F1=T+buoy_param.m*g;
syms Hw
F=0.625*(2*buoy_param.r)*(buoy_param.h-Hw)*v1*v1;
Hw=solve(Hw==(F1+F*tand(theta0))/(rho*(pi*buoy_param.r*buoy_param.r)*g));
Hw=double(vpa(Hw,6));
F_f=matlabFunction(F);
F=F_f(Hw);
%3、浮标受到的风力
%% 系统建立
% 第一段悬链方程
%将整个系统看成整体外力为风力F 那么锚受到的拉力为T 由于系统相对静止有
T=F;
a1=T/w0;a2=T/(w3/barrel.L);a3=T/(w2/tube.L);
y1=f(a1,x0,0,theta0,0);
s1=s(a1,x0,theta0,0);
if isplot==1
    figure,fplot(y1);
    xlim([0,5]);
    ylim([0,5]);
    figure,fplot(s1);
    xlim([0,5]);
    ylim([0,5]);
end
% 第二段悬连线
%第一段悬连线终点为(x0,y0) 则这一段长度为s1(x0) 第二段悬连线起点为(x0,y0)斜率为tan(theta1)
%Q0点竖直方向上受锚链和重物球的重量
theta1=atand((L*w0+w1)/F);
beta1=90-theta1;
% 第三段悬连线
%Q1点竖直方向上受锚链、重物球和钢桶的重量
theta2=atand((L*w0+w1+w3)/F);
beta2=90-theta2;
%%求解连接横坐标
syms x0 x1 x5
y1_f=matlabFunction(y1);%将符号转化为函数求函数值
y2=f(a2,x0,y1_f(x0),theta1,0);
%sym2latex(vpa(y2,4),4);
y2_f=matlabFunction(y2);
y3=f(a3,x1,y2_f(x1,x0),theta2,0);
%sym2latex(vpa(y3,3),5);
y3_f=matlabFunction(y3);
s2=s(a2,x0,theta1,0);
s2_f=matlabFunction(s2);
s3=s(a3,x1,theta2,0);
s3_f=matlabFunction(s3);
eq_set=[y3_f(x5,x0,x1)-(H-Hw);s2_f(x1,x0)-1;s3_f(x5,x1)-4];
if isplot==1
   sym2latex(vpa(eq_set,6),6);
end
x=Newton_iteration(eq_set,L*[1;2;3],0.001);
%% 反求第一段实际悬连线长度
s1_f=matlabFunction(s1);
S0=s1_f(x(1));
theta=[theta0,theta1,theta2];
a=[a1,a2,a3];
end