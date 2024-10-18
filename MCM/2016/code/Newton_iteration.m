function [x0] = Newton_iteration(F,x0,eps)
%Newton_iteration 非线性方程组牛顿迭代法
% eps迭代精度
% F的雅可比矩阵 by 水林
    dF=jacobian(F);
    df=matlabFunction(dF);
    f=matlabFunction(F);
    while 1
        dx=-inv(df(x0(1),x0(2),x0(3)))*f(x0(1),x0(2),x0(3));
        if abs(sum(dx))<eps
          break
        end
        x0=x0+dx;
    end
end