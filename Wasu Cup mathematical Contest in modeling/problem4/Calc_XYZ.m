function [X,Y,Z] = Calc_XYZ(data,d,k,R)
    %Calc_XYZ 计算刺激值
    % 输入 SX(Y,Z) d k
    X=k*sum(d*data(:,1).*R');
    Y=k*sum(d*data(:,2).*R');
    Z=k*sum(d*data(:,3).*R');
end