clc,clear,close all
% data=xlsread('../附件2.xlsx','C4:R27');
% save('data.mat',"data");
load("data.mat");
x=[0.05,0.1,0.5,1,2,3,4,5]*0.01;%8
lamda_sets=400:20:700;
ans=[];
poly_Coefficients_r=[];
poly_Coefficients_y=[];
poly_Coefficients_b=[];
for i=1:size(data,2)
    red=data(1:length(x),i);
    yellow=data(1+length(x):2*length(x),i);
    blue=data(1+2*length(x):3*length(x),i);
    mdl_r=fitlm(x,red);%k/s=a*C+b
    mdl_y=fitlm(x,yellow);
    mdl_b=fitlm(x,blue);
    coeff_r=mdl_r.Coefficients;
    coeff_y=mdl_y.Coefficients;
    coeff_b=mdl_b.Coefficients;

    RS_r=mdl_r.Rsquared.Ordinary;
    RS_y=mdl_y.Rsquared.Ordinary;
    RS_b=mdl_b.Rsquared.Ordinary;

    ans_r=table2array(coeff_r(:,1));
    ans_y=table2array(coeff_y(:,1));
    ans_b=table2array(coeff_b(:,1));
    temp=[lamda_sets(i),ans_r',RS_r,ans_y',RS_y,ans_b',RS_b];
    ans=[ans;temp];
    poly_Coefficients_r=[poly_Coefficients_r,ans_r];
    poly_Coefficients_y=[poly_Coefficients_y,ans_y];
    poly_Coefficients_b=[poly_Coefficients_b,ans_b];
end
name={'Wave Length','red_b','red_x','red_R^2','yellow_b','yellow_x','yellow_R^2','blue_b','blue_x','blue_R^2'};
Table=table(ans(:,1),ans(:,2),ans(:,3),ans(:,4),ans(:,5),...
    ans(:,6),ans(:,7),ans(:,8),ans(:,9),ans(:,10),'VariableNames',name);
writetable(Table,'problem1_ans.xlsx');
save('poly_coef.mat','poly_Coefficients_r','poly_Coefficients_y','poly_Coefficients_b');