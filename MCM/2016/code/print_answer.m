function [] = print_answer(x0,a,Hw,theta,v)
%print_answer 打印结果
% 始终以钢管和钢桶的中心的角度作为倾斜角
parameters;
alpha=0.15;
%钢桶中点横坐标为:
%x_g=x0(1)+alpha*barrel.L/2;%(x0(1)+x0(1))/2;
x_g=(x0(1)+x0(2))/2;
%第2-3段悬连线导数表达式
syms x;
dy2=sinh((x-x0(1))/a(2)+log((1+sind(theta(2)))/cosd(theta(2))));
dy3=sinh((x-x0(2))/a(3)+log((1+sind(theta(3)))/cosd(theta(2))));
dy2_val=matlabFunction(dy2);
dy3_val=matlabFunction(dy3);
%钢桶倾斜角度
gamma1=90-double(atand(dy2_val(x_g)));
disp(['风速为',num2str(v),'m/s时系统参数为:']);
disp(['钢桶倾斜角度:',num2str(gamma1),'度']);
disp(['锚链与水平面的角度:',num2str(theta(1)),'度']);
dxx=(x0(3)-x0(2))/4;
x_s=x0(2):dxx:x0(3);
gamma2=90-double(atand(dy3_val(x_s(1))));
gamma3=90-double(atand(dy3_val(x_s(2))));
gamma4=90-double(atand(dy3_val(x_s(3))));
gamma5=90-double(atand(dy3_val(x_s(4))));
disp(['第一根钢管倾斜角度:',num2str(gamma2),'度']);
disp(['第二根钢管倾斜角度:',num2str(gamma3),'度']);
disp(['第三根钢管倾斜角度:',num2str(gamma4),'度']);
disp(['第四根钢管倾斜角度:',num2str(gamma5),'度']);
disp(['游动区域半径:',num2str(x0(3)+buoy_param.r),'m']);
disp(['浮标吃水深度:',num2str(Hw),'m']);
end