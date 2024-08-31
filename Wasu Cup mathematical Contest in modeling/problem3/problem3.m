% clc,clear,close all
% % 导入基底刺激值和目标颜料刺激值
% load('Lab.mat');%样本的Lab
% load('poly_coef.mat');%多项式系数
% load('XYZ_Base.mat');
% % 用什么来配颜料？
% % 计算当前配方下的R
% clc,clear,close all
% load('Lab.mat');%样本的Lab
% load('poly_coef.mat');%多项式系数
% load('XYZ_Base.mat');
% num=3;
% x0=[0,0,0];
% ans_Solution=[];ans_M=[];ans_E=[];
% min_val=1e11;
% min_e_val=1e11;
% min_m=[];
% min_e=[];
% for s=0.1:0.001:0.9
%     Solution=[];M=[];E=[];
%     for i=1:10
%         L0=L(i);
%         a0=a(i);
%         b0=b(i);
%         % 将固定参数传递给 objfun
%     objfun = @(optimInput)obj_fun(optimInput,s,poly_Coefficients_r,...
%         poly_Coefficients_y,poly_Coefficients_b,K_S0,data,X0,Y0,Z0,L0,a0,b0);
%     
%     % 求解
%     [solution,objectiveValue] = ga(objfun,num,[],[],[],[],zeros(num,1));
%     
%     % 清除变量
%     clearvars objfun
%     Solution=[Solution;solution];
%     m=solution(1)*60+solution(2)*63+solution(3)*65;
%     e=restraint(solution,poly_Coefficients_r,poly_Coefficients_y,poly_Coefficients_b,K_S0,data,X0,Y0,Z0,L0,a0,b0);
%     M=[M;m];
%     E=[E;e];
%     % 清除变量
%     clearvars objfun
%     end
%     if sum(M)<min_val&&sum(E)<min_e_val
%         min_val=sum(M);
%         min_e_val=sum(E);
%         disp(['价格:',num2str(min_val),'色差和:',num2str(min_e_val)]);
%         ans_Solution=Solution;ans_M=M;ans_E=E;
%         min_m=[min_m,min_val];
%         min_e=[min_e,min_e_val];
%     end
% end
name={'样品色号','红色','蓝色','黄色','色差','价格'};
index=1:10;
Table=table(index',ans_Solution(:,1)*100,ans_Solution(:,2)*100,ans_Solution(:,3)*100,ans_E,ans_M,'VariableNames',name);
writetable(Table,'problem3_ans.xlsx');
