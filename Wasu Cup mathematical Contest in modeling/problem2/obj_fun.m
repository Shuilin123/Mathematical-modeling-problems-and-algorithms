function [answer] = obj_fun(optimInput,poly_coef_r,poly_coef_y,poly_coef_b,K_S0,data,X0,Y0,Z0,L,a,b)
    % obj_fun 目标函数
    % poly_coef 多项式系数
    % C_r,C_y,C_b 配色方案
    % 目标样本R值
    % step1:按照配方生成不同波长的K/S值
    C_r=optimInput(1);%燃料浓度
    C_b=optimInput(2);
    C_y=optimInput(3);
    K_S_r=Calc_K_S(poly_coef_r,C_r);
    K_S_b=Calc_K_S(poly_coef_b,C_b);
    K_S_y=Calc_K_S(poly_coef_y,C_y);
    K_S=K_S0+(C_r*K_S_r+C_b*K_S_b+C_y*K_S_y);
    R_=1+K_S-sqrt(K_S.^2+2*K_S);% R_估计的R
    d=20;k=0.1;
    [x,y,z]=Calc_XYZ(data,d,k,R_);
    [L_,a_,b_]=Calc_Lab(x,y,z,X0,Y0,Z0);
    answer=Calc_SeCha(L,a,b,L_,a_,b_);
end