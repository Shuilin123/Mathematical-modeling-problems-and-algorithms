function [U] = solve_pde(x,a,lamda,T,T0,all_time,d)
    %obj_fun 二维热传导方程离散形式
    %   此处提供详细说明
    %这个是数据十分关键
    h=0.1;tao=1;
    r=1e6*a*tao/(h*h);
    len_layer=length(r);
    %环境温度
    m=all_time/tao;
    N=round(d/h);
    ind=[0];
    for i=1:len_layer
        ind=[ind,sum(N(1:i))];
    end
    ke=x(1);
    ks=x(2);
    %计算稳态温度
    x=(1/ks)*T+(1/ke+sum(d./lamda))*T0;
    y=(1/ks+1/ke+sum(d./lamda));
    um=x/y;
    U=zeros(sum(N)+1,m);
    U(:,1)=T0;%任何位置在没有进入实验之前都是体温
    U(1,:)=T;%不论什么时刻与外界接触的面积都是环境温度
    %依赖最后一行
    U(1)=T0;
    for t=2:all_time
        U(sum(N)+1,t)=(1-ks)*U(sum(N)+1,t-1)+ks*um;
    end
    %第一层
    a={};b={};c={};
    for i=1:len_layer
        a1=-r(i)*ones(1,N(i)-2);
        b1=(1+2*r(i))*ones(1,N(i)-1);
        c1=a1;
        a{i}=a1;
        b{i}=b1;
        c{i}=c1;
    end
    %更新
    for t=2:m
        %第一层 1:7
        for layer=1:len_layer
           d1=U(ind(layer)+2:ind(layer+1),t-1);
           d1(1)=d1(1)+r(layer)*U(ind(layer)+1,t-1);
           d1(N(layer)-1)=d1(N(layer)-1)+r(layer)*U(ind(layer+1)+1,t-1);
           U(ind(layer)+2:ind(layer+1),t)=After_Penalty(a{1,layer},b{1,layer},c{1,layer},d1);
        end
        for inner_layer=1:len_layer-1
              U(ind(inner_layer+1)+1,t)=(lamda(inner_layer)*U(ind(inner_layer+1),t)+lamda(inner_layer+1)*U(ind(inner_layer+1)+2,t))/(lamda(inner_layer)+lamda(inner_layer+1));
        end
    end
end