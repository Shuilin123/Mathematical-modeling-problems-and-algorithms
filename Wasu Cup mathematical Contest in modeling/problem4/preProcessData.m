clc,clear,close all
d=20;
k=0.1;
data=xlsread('..\附件1.xlsx','B4:D19');
K_S0=xlsread('..\附件2.xlsx','C3:R3');
data2=xlsread('..\附件3.xlsx','B3:Q12');
%计算10个目标样本的刺激值
X=[];Y=[];Z=[];
for i=1:size(data2,1)
    [x,y,z]=Calc_XYZ(data,d,k,data2(i,:));
    X=[X;x];Y=[Y;y];Z=[Z;z];
end
%% 计算基材的X0,Y0,Z0
% K/S 计算基材的R0
R0=1+K_S0-sqrt(K_S0.*K_S0+2*K_S0);
[X0,Y0,Z0]=Calc_XYZ(data,d,k,R0);
save('XYZ_Base.mat','X0','Y0','Z0','K_S0');
save('XYZ.mat','X','Y','Z');
% 计算10个样本的L a b
L=[];a=[];b=[];
for i=1:size(data2,1)
    [l,aa,bb]=Calc_Lab(X(i),Y(i),Z(i),X0,Y0,Z0);
    L=[L,l];
    a=[a,aa];
    b=[b,bb];
end
%样本的L a b
save('Lab.mat','L','a','b','data');