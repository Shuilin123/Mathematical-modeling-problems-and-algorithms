function [error] = obj_fun(ks,u0,um)
%obj_fun 寻找与空气的传热系数
%   此处提供详细说明
    tn=length(um);
    u=zeros(1,tn);
    u(1)=u0;
    for t=2:tn
        u(t)=(1-ks)*u(t-1)+ks*um(tn);
    end
    error=sum((u-um').^2)/2;
end