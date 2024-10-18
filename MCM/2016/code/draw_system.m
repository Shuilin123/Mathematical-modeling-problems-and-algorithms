function [] = draw_system(a,theta,L,S0,x,Hw,v)
%draw_system 画系泊系统
%   此处提供详细说明
parameters;
y1=f(a(1),L-S0,0,theta(1),0);
y1_val=matlabFunction(y1);
y2=f(a(2),x(1),y1_val(x(1)),theta(2),0);
y2_val=matlabFunction(y2);
y3=f(a(3),x(2),y2_val(x(2)),theta(3),0);
%=figure('Name',['风速：',str,'m/s']),
fplot(y1,[L-S0,x(1)],'Color','r');
hold on
plot([0,L-S0],[0,0],'Color','r');
hold on
fplot(y2,[x(1),x(2)],'Color','b');
hold on
fplot(y3,[x(2),x(3)],'Color','g');
hold on
plot([0,x(3)+5],[H,H],'LineStyle','--');
hold on
fill([x(3)-buoy_param.r,x(3)+buoy_param.r,x(3)+buoy_param.r,x(3)-buoy_param.r],[H-Hw,H-Hw,H+(buoy_param.h-Hw),H+(buoy_param.h-Hw)],[0.75;0.75;0.75;0.75]);
hold on
plot([x(1),x(1)],[y2_val(x(1))-3,y2_val(x(1))],'Color','k');
hold on
scatter(x(1),y2_val(x(1))-3,150,0.5,'filled');
hold on
scatter(L-S0,0,25,0,"filled");
hold on
scatter(x(1),y1_val(x(1)),25,0,"filled");
hold on
scatter(x(2),y2_val(x(2)),25,0,"filled");
hold on
scatter(x(3),H-Hw,25,0,"filled");
hold on
scatter(0,0,25,0,"filled")
hold on
txt=['v=',num2str(v),'m/s'];
text(1.5,H+2,txt)
txt=['\rightarrow'];
for i=H+0.5:0.5:H+4.5
  text(0.5,i,txt,'LineWidth',40)
end
xlim([0,x(3)+5]);
ylim([0,H+5]);
hold off
end