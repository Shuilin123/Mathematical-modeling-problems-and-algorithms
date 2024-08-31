function [val] = obj_fun(optimInput,s,poly_coef_r,poly_coef_y,poly_coef_b,K_S0,data,X0,Y0,Z0,L,a,b)
%obj_fun 目标函数
%val 原料钱
    M=1e10;
    z=restraint(optimInput,poly_coef_r,poly_coef_y,poly_coef_b,K_S0,data,X0,Y0,Z0,L,a,b);
    val=optimInput(1)*60+optimInput(2)*63+optimInput(3)*65+M*max(z,s)-M*min(z,1e-10);
end