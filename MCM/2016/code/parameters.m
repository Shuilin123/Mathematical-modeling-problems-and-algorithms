%%1、浮标
buoy_param.m=1000; %质量 kg
buoy_param.r=2/2;    %底面直径 m
buoy_param.h=2;    %高 m
%%2、钢管
tube.n=4;   %数量
tube.L=1;   %长度 m
tube.r=((50/2)*1.0e-3); %底面半径 m
tube.m=10;  %质量 kg
%%3、缸桶
barrel.m=100; %质量 kg
barrel.L=1;   %长度 m
barrel.r=(30/2)*1.0e-2;  %外径 m
%%4、锚链
chain.L=[78,105,120,150,180]*1.0e-3; %长度 m
chain.w=[3.2,7,12.5,19.5,28.12];%比重 kg/m
%%其他参数
H=18;        %海平面与锚的距离
g=9.8;       %重力加速度 m/s^2(N/kg)
rho_steel=7.8*1e3; %钢的比重
rho=1.025*1e3;%rho海水密度 kg/m^3