function [yx] = f(a1,x1,y1,theta1,isplot)
%%y 悬连线方程
% a:F/w0
% (y(x0)=y0,y'(x0)=tan(theta0)) 起点坐标
% syms y(x);
% dy=diff(y);
% y=dsolve(diff(dy)==(1/a)*sqrt(1+dy^2),y(x0)==y0,dy(x0)==tan(theta0));
% y=simplify(y); %把计算结果化解
% y=y(1,1);
syms x x0 y0 theta0 a;
y=a*cosh((x-x0)/a+log((1+sin(theta0))/cos(theta0)))+y0-a/cos(theta0);
if isplot==1
   sym2latex(y,1);
end
yx=a1*cosh((x-x1)/a1+log((1+sind(theta1))/cosd(theta1)))+y1-a1/cosd(theta1);
end