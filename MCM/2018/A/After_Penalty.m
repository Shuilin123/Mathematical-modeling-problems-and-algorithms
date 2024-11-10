function [x] = After_Penalty(a,b,c,d)
    % 输入参数：
    % a - 下对角线元素（长度为 n-1）
    % b - 主对角线元素（长度为 n）
    % c - 上对角线元素（长度为 n-1）
    % d - 右侧常数向量（长度为 n）
    %
    % 输出参数：
    % x - 解向量（长度为 n）
 
    n = length(b);
    if length(a) ~= n-1 || length(c) ~= n-1 || length(d) ~= n
        error('输入向量长度不匹配');
    end
 
    % 初始化c'和d'数组
    c_prime = zeros(n, 1);
    d_prime = zeros(n, 1);
    
    % 设定初始值
    c_prime(1) = c(1) / b(1);
    d_prime(1) = d(1) / b(1);
    
    % 逐行计算c'和d'
    for i = 2:n
        denominator = b(i) - a(i-1) * c_prime(i-1);
        if denominator == 0
            error('分母为零，无法求解');
        end
        try
        c_prime(i) = c(i) / denominator;
        catch
            dsg=0;
        end
        d_prime(i) = (d(i) - a(i-1) * d_prime(i-1)) / denominator;
    end
    
    % 回代求解x
    x = zeros(n, 1);
    x(n) = d_prime(n);
    for i = n-1:-1:1
        x(i) = d_prime(i) - c_prime(i) * x(i+1);
    end
end