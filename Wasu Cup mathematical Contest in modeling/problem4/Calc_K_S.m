function [K_S] = Calc_K_S(poly_coef,c)
%Calc_K_S 按照浓度生成不同波长的K/S值
%输入：poly_coef拟合式系数 c为待计算浓度
%输出：K_S
K_S=poly_coef(1,:)+c*poly_coef(2,:);
end