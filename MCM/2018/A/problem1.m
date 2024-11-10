clc,clear,close all
Data1=xlsread('CUMCM-2018-Problem-A-Chinese-Appendix.xlsx','附件1','B3:E6');
Data2=xlsread('CUMCM-2018-Problem-A-Chinese-Appendix.xlsx','附件2','B3:B5403');
temperature=Data2(2:end,1);
Data1(2,4)=6;
Data1(4,4)=5;
lamda=Data1(:,3);
a=lamda./(Data1(:,1).*Data1(:,2));
l=Data1(:,4);
%这个是数据十分关键
h=0.1;tao=1;
r=1e6*a*tao/(h*h);
%环境温度
T=75;T0=37;%没有开始实验前温度都为人体温度
all_time=90*60;
m=all_time/tao;
N=round(l/h);
objfun=@(optimInput)obj_fun(optimInput,T0,temperature);
options = optimoptions('ga','ConstraintTolerance',1e-20,'PlotFcn', @gaplotbestf);

[ks,obj_value]=ga(objfun,1,[],[],[],[],zeros(1,1),1*ones(1,1),[],options);
%计算ke
ux=temperature(length(temperature));
ke_=(1/ks)*((T-ux)/(ux-T0))-sum(l./lamda);
ke=1/ke_;
save('paramters.mat','ke','ks','Data1');
U=solve_pde([ke,ks],a,lamda,T,T0,all_time,l);

figure('Name','温度分布');
mesh(U);
xlabel('时间/s');
ylabel('长度/dmm');
zlabel('温度/摄氏度');
figure('Name','皮肤外侧温度变化');
plot(U(end,:));
hold on
plot(temperature);
legend('Actual temperature','Calculate temperature');
xlabel('时间/s');
ylabel('温度/摄氏度');

