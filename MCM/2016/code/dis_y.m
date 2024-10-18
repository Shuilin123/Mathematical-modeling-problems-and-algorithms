function [x,y,theta] = dis_y(theta0,f,rho,T0,x0,y0,s0,ds)
%%f 悬连线方程迭代算法
% theta0 迭代初始角度 
% f海中悬连线单位水平力
% T0 水平拉力
% x0,y0 悬连线起始坐标
% s 悬连线长度
% ds 迭代步长
% 误差项
    x=[];
    y=[];
    theta=[];
    s=0;
    while 1
     theta=[theta,theta0];
     theta0=theta0+ds*(f*sind(theta0)^2+rho*cosd(theta0))/T0;
     T0=T0+(rho*sind(theta0)-f*sind(theta0)*cosd(theta0))*ds;
     s=s+ds;
     if s0<s
         break;
     end
     x=[x,x0];
     y=[y,y0];
     x0=x0+cosd(theta0)*ds;
     y0=y0+sind(theta0)*ds;
    end
end