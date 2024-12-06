clc,clear,close all
alpha=1.5;
theta=60;
beta=0:45:315;
D=120;
delta_d=0.3;
u_int=1852;
d=[0:delta_d:2.1]*u_int;
m=length(beta);n=length(d);
h=zeros(m,n);
for i=1:m
    for j=1:n

       h(i,j)=D-d(j)*cosd(pi-beta(i))*tand(alpha);
    end
end
W=zeros(m,n);
for i=1:m
    for j=1:n
        gammax=atand(tand(alpha)*abs(sind(beta(i))));
        L1=h(i,j)*sind(theta)/cosd(theta+gammax);
        L2=h(i,j)*sind(theta)/cosd(theta-gammax);
        W(i,j)=L1+L2;
    end
end
writematrix(W,'../result2.xlsx','Sheet',1,'Range','C3:J10');
