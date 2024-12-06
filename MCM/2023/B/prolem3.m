clc,clear,close all
a=4*1852;
b=2;
alpha=1.5;
theta=60;
D=110;
eta=0.1;
min_val=1e10;x_=[];
h0=D-(a/2)*tand(alpha);
y0=h0*tand(60);
h1=h0+y0*tand(alpha);
L1=h1*(sind(theta))/cosd(theta+alpha);
L2=h1*(sind(theta))/cosd(theta-alpha);
P=y0/cosd(alpha);
A=(1/cosd(alpha)-sind(theta)*tand(alpha)/cosd(theta-alpha));
y=[];
y=[y,y0];
ans=0;
h1=h0;
for i=1:5000
   y1=(P+L1-eta*(L1+L2)+sind(theta)*h0/cosd(theta-alpha))/A;
   if y1>a
       break;
   end
   y=[y,y1];
   P=y1/cosd(alpha);
   h1=h0+y1*tand(alpha);
   L1=h1*(sind(theta))/cosd(theta+alpha);
   L2=h1*(sind(theta))/cosd(theta-alpha);
   ans=ans+(L1+(y1-y0)+L2);
   y0=y1;
end
for i=0:0.01:2
   plot(y,i*ones(size(y)),'.');
   hold on
end
grid on
xlabel('射线宽度(m)');
ylabel('射线长度(海里)')