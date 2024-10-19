clc,clear,close all;
%1、假设当风力为v时锚链恰好被拉起(即x0=0,y0=0)
eps=0.002;  %锚链于水平方向的夹角误差为2g
id=2;%id锚链号
L=22.05;%L锚链长度
M=1200;%M重物球质量 kg
rho=1.025*1e3;%rho海水密度 kg/m^3
v1=36;%风速度  m/s
[theta0]=binnarySerach(id,L,M,rho,v1,0);
[x,~,theta,a,Hw]=solve1(id,L,M,rho,v1,0,theta0,0);
print_answer(x,a,Hw,theta,v1);
left=M+1;right=3*M;
eps_theta0=16-0.1;%误差为0.1度 % 15.9
%二分查找找0点
tic
while 1
    mid=(left+right)/2;
    [theta0_l]=binnarySerach(id,L,left,rho,v1,0);
    [theta0_m]=binnarySerach(id,L,mid,rho,v1,0);
    [x0,~,theta,a,~]=solve1(id,L,mid,rho,v1,0,theta0_m,0);
    x_g=(x0(1)+x0(2))/2;
    %第2-3段悬连线导数表达式
    syms xs;
    dy2=sinh((xs-x0(1))/a(2)+log((1+sind(theta(2)))/cosd(theta(2))));
    dy2_val=matlabFunction(dy2);
    gamma_m=90-double(atand(dy2_val(x_g)));
    val1=theta0_l-eps_theta0;
    val3=theta0_m-eps_theta0;
    if abs(val3)<eps
       break;
    end
    if val1*val3<0 %零点在左半区间
       right=mid;
    else
       left=mid; %零点在左半区间 
    end
    disp(['重物球为',num2str(mid),'kg时，钢桶倾斜角度:',num2str(gamma_m),'度']);
    disp(['锚链与水平方向的夹角为：',num2str(theta0_m),'度']);
end
toc
[theta0]=binnarySerach(id,L,mid,rho,v1,0);
[x,S0,theta,a,Hw]=solve1(id,L,M,rho,v1,0,theta0,0);
draw_system(a,theta,L,S0,x,Hw,v2);
print_answer(x,a,Hw,theta,v2);