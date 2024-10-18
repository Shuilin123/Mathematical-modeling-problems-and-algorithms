function [mid] = binnarySerach(id,L,M,rho,v1,x0)
  %binnarySerach 二分搜索theta0
  left=0;right=88;
  while 1
    mid=(left+right)/2;
    [~,S0,~,~,~]=solve1(id,L,M,rho,v1,x0,left,0);
    [~,S2,~,~,~]=solve1(id,L,M,rho,v1,x0,mid,0);
    val1=L-S0;
    val3=L-S2;
    if abs(left-mid)<0.001
       break;
    end
    if val1*val3<0 %零点在左半区间
       right=mid;
    else
       left=mid; %零点在左半区间 
    end
  end
end