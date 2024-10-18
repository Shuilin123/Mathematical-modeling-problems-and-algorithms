clc,clear,close all
v=1.5; %水流速度m/s
v1=36; %风速度 m/s
M=1200;%重物球
H=20;  %水深20m
id=2;
n=345;
theta0=16;
%给定重物球质量锚链长度
DisSystem(v,v1,M,H,theta0,id,n);

