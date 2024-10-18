function [v] = argmax_sovle1(id,L,M,rho,v1,v2,step,eps)
%argmax_sovle1 求解满足条件最大v
%
    S0=0;
    for v=v1:step:v2
        [~,S0,~,~,~]=solve1(id,L,M,rho,v,L-S0,0,0);
        %当前的绳索与实际绳索之差小于1cm 
        if L>=S0&&L-S0<eps
            break;
        end
        if mod(v*100,10)==0
           disp(['当前长度未拉起绳索长度为:',num2str(L-S0),'m']);
        end
    end
end