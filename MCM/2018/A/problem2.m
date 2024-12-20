clc,clear,close all
load('paramters.mat');
Data1(2,4)=6;
Data1(4,4)=5.5;
lamda=Data1(:,3);
a=lamda./(Data1(:,1).*Data1(:,2));
l=Data1(:,4);
%环境温度
T=65;T0=37;%没有开始实验前温度都为人体温度
t=60;
uint_t=60;
all_time=t*uint_t;%工作时长
u_max=47;
u_=44;t_=5;
left=0.6;
right=25;
left_ks=0.01*ks;right_ks=ks;
while left<=right %遍历最优厚度
   if right-left<0.01
       break;
   end
   mid=(left+right)/2;
   mid_ks=(left_ks+right_ks)/2;
   disp(['d2:',num2str([left,right])]);
   l(2)=mid;
   ke_=(1/mid_ks)*((T-u_max)/(u_max-T0))-sum(l./lamda);
   U=solve_pde([1/ke_,mid_ks],a,lamda,T,T0,all_time,l);
   [ln,tn]=size(U);
   t2=t_*uint_t;
   if U(ln,all_time)<=u_max&&U(ln,all_time-t2)<=u_
        right=mid;
        left_ks=mid_ks;
   else
        left=mid;
        right_ks=mid_ks;
   end
end
figure('Name','温度分布');
mesh(U);
xlabel('长度/dmm');
ylabel('时间/s');
zlabel('温度/摄氏度');
figure('Name','皮肤侧温度');
plot(U(end,:));
hold on
plot(ones(1,all_time)*max(U(end,:)));
hold on
plot(ones(1,all_time)*u_);
hold on
plot(all_time-t2:all_time,U(end,all_time-t2:all_time),'LineWidth',3,'Color','b');
legend('temp',['T=',num2str(max(U(end,:)))],['T=',num2str(u_)]);
ylabel('温度/摄氏度');
xlabel('时间/s');