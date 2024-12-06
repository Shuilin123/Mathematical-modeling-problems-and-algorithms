clc,clear,close all
alpha=1.5;
theta=60;
D=70;
d=-800:200:800;
h=D-d*tand(alpha);
L1=h*sind(theta)/cosd(theta+alpha);
L2=h*sind(theta)/cosd(theta-alpha);
W=L1+L2;
d_=(d(2)-d(1))/cosd(alpha);
eta=[];
for i=1:length(d)-1
    LX=W(i)+W(i+1);
    LY=LX-(d_+L1(i)+L2(i+1));% 重叠长度
    eta=[eta,LY/(W(i+1))*100];
end
writematrix(h,'../result1.xlsx','Sheet',1,'Range','B2:J2');
writematrix(W,'../result1.xlsx','Sheet',1,'Range','B3:J3');
writematrix(eta,'../result1.xlsx','Sheet',1,'Range','C4:J4');