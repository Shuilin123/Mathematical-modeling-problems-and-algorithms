function [L,a,b] = Calc_Lab(X,Y,Z,X0,Y0,Z0)
%Calc_Lab 计算L、a、b
% 输入基材和颜色材料的刺激值
    if Y/Y0>0.008856 && X/X0>0.008856 && Z/Z0>0.008856
        L=116*(Y/Y0)^(1/3)-16;
        a=500*((X/X0)^(1/3)-(Y/Y0)^(1/3));
        b=200*((Y/Y0)^(1/3)-(Z/Z0)^(1/3));
    else
        L=903.3*(Y/Y0);
        a=3893.5*((X/X0)-(Y/Y0));
        b=1557.4*((Y/Y0)-(Z/Z0));
    end
end