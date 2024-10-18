function [] = DisSystem(v,v1,M,H,theta0,id,n)
%%DisSystem 离散系统
%v 海水速度 m/s
%v1 风速   m/s
%M  重物球质量 kg
%H  海水深度   m
%id 锚链标号
%n  锚链链节数量 
    parameters;
    %% 导出参数
    %% 单位长度各部件水流力
    h=1;%单位长度m
    %1.浮标
    f0=374*v*v*(2*buoy_param.r*h);
    %2.钢桶
    f1=374*v*v*(2*barrel.r*h);
    %3.钢管
    f3=374*v*v*(2*tube.r*h);
    %4.重物球
    %体积
    V=M/rho_steel;
    %水中所受重力为
    f=M*g-rho*V*g;
    r=((3*V)/(4*pi))^(1/3);
    f4=374*pi*r*r*v*v;
    %4.锚链
    V=chain.w(id)/rho_steel;
    S=V/h;
    r=sqrt(S/pi);
    f5=374*2*r*h*v*v;
    %1、计算各个部件在海水中的重量 锚链体积忽略不计
    w0=chain.w(id)*g-rho*(chain.w(id)/rho_steel)*g;% 锚链单位重量
    w1=M*g-rho*(M/(rho_steel))*g;% 重物球重量
    %每节钢管在水中的重量
    w2=tube.m*g-rho*(tube.m/rho_steel)*g;
    %钢桶在海水中的重量
    w3=barrel.m*g-rho*(pi*barrel.r*barrel.r*barrel.L)*g; 
    %% 悬链线求解
    %%1、浮标所受水平力
    ds=0.001;%每次迭代1mm
    x0=0;
    y0=0;
    %浮标所受拉力T为:
    L=chain.L(id)*n;
    T=L*w0+w1+tube.n*w2+w3;
    %浮标所受浮力为
    F1=T+buoy_param.m*g;
    syms Hw
    F=0.625*(2*buoy_param.r)*(buoy_param.h-Hw)*v1*v1+Hw*f0;%加上水流力
    Hw=solve(Hw==(F1+F*tand(theta0))/(rho*(pi*buoy_param.r*buoy_param.r)*g));
    Hw=double(vpa(Hw,6));
    F_f=matlabFunction(F);
    F1=F_f(Hw);
    %%求锚点水平力=浮标水平力+重物球水平力+钢管水平力+钢桶水平力+链水平力(初步F) 
        Fx=F1+f4+f1*barrel.L+f3*tube.L*tube.n+f5*L;
        Fy=Fx*tand(theta0);
        F=sqrt(Fx^2+Fy^2);
        [x,y,theta] = dis_y(theta0,f5,w0,F,0,0,L,0.01);
        figure,plot(x,y);
        xlim([0,x(end)]);
        ylim([0,y(end)]);
        figure,plot(theta);
end