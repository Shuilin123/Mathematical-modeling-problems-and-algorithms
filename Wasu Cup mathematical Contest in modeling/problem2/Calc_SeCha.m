function [delta_E] = Calc_SeCha(L1,a1,b1,L2,a2,b2)
    %Calc_SeCha 计算色差
    % 待计算色差的量样品的L a b值
    delta_L=L1-L2;
    delta_Cs=sqrt(a1^2+b1^2)-sqrt(a2^2+b2^2);
    delta_Cc=sqrt((a1-a2)^2+(b1-b2)^2);
    delta_H=sqrt(delta_Cc^2-delta_Cs^2);
    delta_E=sqrt(delta_L^2+delta_Cs^2+delta_H^2);
end