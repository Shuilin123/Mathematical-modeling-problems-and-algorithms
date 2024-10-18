clc,clear,close all
%1、假设当风力为v时锚链恰好被拉起(即x0=0,y0=0)
eps=0.01;  %锚链误差为1cm
id=2;%id锚链号
L=22.05;%L锚链长度
M=1200;%M重物球质量 kg
rho=1.025*1e3;%rho海水密度 kg/m^3
v1=12;%风速度  m/s
[~,S0,~,~,~]=solve1(id,L,M,rho,v1,0,0,0);
S1=L-S0;
disp(['未拉起绳索长度为:',num2str(S1),'m']);
%由实际悬连线长度S0重新计算
[x,S0,theta,a,Hw]=solve1(id,S0,M,rho,v1,L-S0,0,0);
figure('Name','风速12m/s');
draw_system(a,theta,L,S0,x,Hw,v1);
print_answer(x,a,Hw,theta,v1);
v2=24; %风速2
%求解刚好把锚链拉起的风速
if exist('./v.mat')
   load('./v.mat');
else
   [v] = argmax_sovle1(id,L,M,rho,12,v2,0.01,0.01);
   save('./v.mat','v');%防止重复计算
end
[theta0]=binnarySerach(id,L,M,rho,v2,0);
[x,S0,theta,a,Hw]=solve1(id,L,M,rho,v2,0,theta0,0);
fig=figure('Name','风速24m/s');
draw_system(a,theta,L,S0,x,Hw,v2);
print_answer(x,a,Hw,theta,v2);
%% 风力逐渐增大悬连线方程
x=[],S0=[],theta=[],a=[],Hw=[];
S0x=L;
% 当风速v0<=v时
for v0=v1:0.1:v
    disp(['当前速度为:',num2str(v0),'m/s']);
    [xx,S0x,thetax,ax,Hwx]=solve1(id,S0x,M,rho,v0,L-S0x,0,0);
    x=[x,xx];
    S0=[S0,S0x];
    theta=[theta,thetax'];
    a=[a,ax'];
    Hw=[Hw,Hwx];
end
% 当风速v0>v时
for v0=v+0.1:0.1:v2
   disp(['当前速度为:',num2str(v0),'m/s']);
   %优化theta0
   optim_theta0=binnarySerach(id,L,M,rho,v1,0);
   %用优化的theta0求解系统
   [xx,S0x,thetax,ax,Hwx]=solve1(id,L,M,rho,v0,0,optim_theta0,0);
   x=[x,xx];
   S0=[S0,S0x];
   theta=[theta,thetax'];
   a=[a,ax'];
   Hw=[Hw,Hwx];
end
figure('Name','风速12-24m/s');
v=v1:0.1:v2;
for i=1:length(Hw)
   draw_system(a(:,i),theta(:,i),L,S0(i),x(:,i),Hw(i),v(i));
   drawnow;
end
