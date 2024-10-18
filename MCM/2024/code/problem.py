# -*- coding: utf-8 -*-
"""
Created on Mon Sep 16 08:59:39 2024

@author: dell
"""
import numpy as np
import pandas as pd
import time
import pyomo.environ as pyo
from pyomo.opt import SolverFactory
from itertools import chain
import pickle
data1=pd.read_excel('../附件1.xlsx',sheet_name='乡村的现有耕地');
with open("c.pkl",'rb') as tf:
    c=pickle.load(tf);
with open("d.pkl",'rb') as tf:
    d=pickle.load(tf);
with open("q.pkl",'rb') as tf:
    q=pickle.load(tf);
with open("dmand.pkl",'rb') as tf:
    dmand=pickle.load(tf);

A=data1['地块面积/亩'].values;
min_S=min(A);
#最小块的面积
min_S=min_S.reshape(1,-1)/3;
#获取数据
min_S=min_S[0];
min_S=min_S[0];
#记录时间
startTime=time.time();
## 定义基本参数
N=41;#粮食种类
J=2;#季度数
#旱地
Dry_N=6;
#梯田
Terr_N=14;
#山坡地
Hill_N=6;
#水浇地
Irri_N=8;
#普通大棚 
Comm_N=16;
#智慧大棚
Smart_N=4;
# 地块数
S=Dry_N+Terr_N+Hill_N+Irri_N+Comm_N+Smart_N;
#粮食集合1数量
grain_n1=15;
#粮食集合2数量
grain_n2=1;
#粮食集合3数量
grain_n3=18;
#粮食集合4数量
grain_n4=3;
#粮食集合5数量
grain_n5=4;
t_max=2030-2023;
endTime=time.time();
def OptimalProblem():
    #定义大数
    Big_M=99999999;
    ##定义具体模型
    model=pyo.ConcreteModel();
    model.name='Planting Strategy'
    #定义年份
    t=set(range(1,1+t_max));
    ##定义粮食集合
    #粮食集合1数量
    model.grain1=set(range(1,1+grain_n1));
    Ns=grain_n1
    #粮食集合2数量
    model.grain2=set([Ns+1]);
    Ns=Ns+1;
    #粮食集合3数量
    model.grain3=set(range(Ns+1,Ns+grain_n3+1));
    Ns=Ns+grain_n3;
    #粮食集合4数量
    model.grain4=set(range(Ns+1,Ns+grain_n4+1));
    Ns=Ns+grain_n4;
    #粮食集合5数量
    model.grain5=set(range(Ns+1,Ns+grain_n5+1));
    #豆类
    model.grain6=set([1,2,3,4,5]);
    model.grain7=set([17,18,19]);
    ##定义地块类型集合
    #干旱地
    model.Dry=set(range(1,Dry_N+1));
    Ns=Dry_N;
    #梯田
    model.Terr=set(range(Ns+1,Ns+Terr_N+1));
    Ns=Ns+Terr_N;
    #山坡地
    model.Hill=set(range(Ns+1,Ns+Hill_N+1));
    Ns=Ns+Hill_N;
    #水浇地
    model.Irri=set(range(Ns+1,Ns+Irri_N+1));
    Ns=Ns+Irri_N;
    #普通大棚 
    model.Comm=set(range(Ns+1,Ns+Comm_N+1));
    Ns=Ns+Comm_N+1;
    #智慧大棚
    model.Smart=set(range(Ns,Ns+Smart_N));
    ##定义决策变量
    #第k年编号为j的土地种植i号作物的面积为x(i,j,k) 为非负实数
    model.I=set(range(1,N+1));
    model.J=set(range(1,S+1));
    model.K=set(range(1,J+1));
    model.T=set(range(1,t_max+1));
    model.x=pyo.Var(model.I,model.J,model.K,model.T,domain=pyo.NonNegativeReals);
    #第k年编号为j的土地种植i号作物的为y(i,j,k)==1 为非负实数
    model.y=pyo.Var(model.I,model.J,model.K,model.T,domain=pyo.Binary);
    
    ## 约束条件
    model.con=pyo.ConstraintList();
    #单季度约束
    #def contirans(model):
    for k in t:
        ##单季度约束
        #干旱地
        for j in model.Dry:
            #第一度季度至少种一种
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain1)>=1);
        #梯田
        for j in model.Terr:
             #第一度季度至少种一种
             model.con.add(sum(model.y[i,j,1,k] for i in model.grain1)>=1);
        #山坡地
        for j in model.Hill:
             #第一度季度至少种一种
             model.con.add(sum(model.y[i,j,1,k] for i in model.grain1)>=1);
        for j in model.J:
            #1-15号作物不能种在第二季
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain1)==0);
            # i-15无论什么作物都要满足面积约束
            model.con.add(sum(model.x[i,j,1,k] for i in model.grain1)<=A[j-1]);
            model.con.add(sum(model.x[i,j,2,k] for i in model.grain1)<=A[j-1]);
        for j in model.J-(model.Dry|model.Terr|model.Hill):
            #1-15号作物不能种在除干旱地，梯田，山坡地外的地
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain1)==0);
        
        #水稻不能种在除水浇地以外的任何地方
        for j in model.J-model.Irri:
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain2)==0);
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain2)==0);
        #物种17-34不能种在干旱地，梯田，山坡地 和
        for j in model.Dry|model.Terr|model.Hill:
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain3)==0);
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain3)==0);
        ##水浇地
       
        for j in model.Irri:
             #水稻约束
             model.con.add(sum(model.x[i,j,1,k] for i in model.grain2)<=A[j-1]);
             model.con.add(sum(model.x[i,j,2,k] for i in model.grain2)<=A[j-1]);
             #水浇地只能种植一季
             model.con.add(sum(model.y[i,j,2,k] for i in model.grain2)==0);
             #水稻要么种植要么不种
             model.con.add(sum(model.y[i,j,1,k] for i in model.grain2)<=1);
            
             ##分两季种植
             #第一季
             model.con.add(sum(model.x[i,j,1,k] for i in model.grain3)<=A[j-1]);
             model.con.add(sum(model.x[i,j,2,k] for i in model.grain3)<=A[j-1]);
             model.con.add(sum(model.y[i,j,2,k] for i in model.grain3)==0);
             model.con.add(sum(model.y[i,j,1,k] for i in model.grain3)>=1);
             #第二季
             model.con.add(sum(model.x[i,j,2,k] for i in model.grain4)<=A[j-1]);
             model.con.add(sum(model.x[i,j,1,k] for i in model.grain4)<=A[j-1]);
             model.con.add(sum(model.y[i,j,1,k] for i in model.grain4)==0);
             #大白菜和红白萝卜选一种
             model.con.add(sum(model.y[i,j,2,k] for i in model.grain4)==1);
             #要么种植水稻 要么种植两季
             sum1=sum(model.y[i,j,1,k] for i in model.grain3);
             sum2=sum(model.y[i,j,2,k] for i in model.grain4);
             for i in model.grain2:
                 model.con.add(model.y[i,j,1,k]+(sum1+sum2)/2==1);    
        #所有第一季不能种值35-37
        for j in model.J:
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain4)==0);
        #除水浇地外所有第二季不能种值35-37
        for j in model.J-model.Irri:
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain4)==0);
        #只有普通大棚第一季
        ##普通大棚
        for j in model.Comm:
            #第一季
            model.con.add(sum(model.x[i,j,1,k] for i in model.grain3)<=A[j-1]);
            model.con.add(sum(model.x[i,j,2,k] for i in model.grain3)<=A[j-1]);
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain3)==0);
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain3)>=1);
            
            #model.con.add(sum(model.y[i,j,k] for i in grain3)<=1);
            #第二季 食用菌中最少一种
            model.con.add(sum(model.x[i,j,1,k] for i in model.grain5)<=A[j-1]);
            model.con.add(sum(model.x[i,j,2,k] for i in model.grain5)<=A[j-1]);
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain5)==0);
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain5)>=1);
        #所有第一季不能种值38-41
        for j in model.J:
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain5)==0);
        #除普通大棚外所有第二季不能种值38-41
        for j in model.J-model.Comm:
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain5)==0);
        ##智慧大棚
        for j in model.Smart:
            #第一季度
            model.con.add(sum(model.x[i,j,1,k] for i in model.grain3)<=A[j-1]);
            #第二季
            model.con.add(sum(model.x[i,j,2,k] for i in model.grain3)<=A[j-1]);
            #第一季度
            model.con.add(sum(model.y[i,j,1,k] for i in model.grain3)>=1);
            #第二季
            model.con.add(sum(model.y[i,j,2,k] for i in model.grain3)>=1);
        #每种作物不能重茬种植
        for i in model.I:
            for j in model.J:
                #季数不能重茬
                model.con.add(model.y[i,j,1,k]+model.y[i,j,2,k]<=1);
                #年份·不能重茬
                if k<t_max:
                   model.con.add(model.y[i,j,1,k]+model.y[i,j,1,k+1]<=1);
                   model.con.add(model.y[i,j,2,k]+model.y[i,j,2,k+1]<=1);
        for i in model.I:
            for j in model.J:
                model.con.add(model.x[i,j,1,k]+Big_M*(1-model.y[i,j,1,k])>=min_S);
                model.con.add(model.x[i,j,2,k]+Big_M*(1-model.y[i,j,2,k])>=min_S); 
                # 每块地在每一季度 每一年的产量不能超过dmand量
                # if x*d>dmans ->y=1
                model.con.add(dmand[i-1,j-1,0]+Big_M*(1-model.y[i,j,1,k])>=model.x[i,j,1,k]*d[i-1,j-1,0]);
                model.con.add(dmand[i-1,j-1,1]+Big_M*(1-model.y[i,j,2,k])>=model.x[i,j,2,k]*d[i-1,j-1,1]); 
        #每块地在每一季度 每一年只能用一次
        #每隔3年种植一次豆类1 2 3 4 5 单季度
        for j in model.Dry|model.Terr|model.Hill:
            if k+3<=t_max:
               model.con.add(sum(model.y[i,j,1,k]+model.y[i,j,1,k+1]+model.y[i,j,1,k+2] for i in model.grain6)>=1);
        #水浇地第一季度普通（智慧大棚）
        for j in model.Irri|model.Comm|model.Smart:
             if k+3<=t_max:
                model.con.add(sum(model.y[i,j,1,k]+model.y[i,j,1,k+1]+model.y[i,j,1,k+2] for i in model.grain7)>=1);
        #智慧大棚第二季度
        for j in model.Smart:
             if k+3<=t_max:
                model.con.add(sum(model.y[i,j,2,k]+model.y[i,j,2,k+1]+model.y[i,j,2,k+2] for i in model.grain7)>=1);
        
            #return model;
    ## 定义目标函数
    #c  物种 地块类型 季数
    val=sum((model.y[i,j,h,k]*model.x[i,j,h,k])*d[i-1,j-1,h-1]*c[i-1,j-1,h-1]-model.y[i,j,h,k]*model.x[i,j,h,k]*q[i-1,j-1,h-1] \
            for k in model.T for i in model.I for j in model.J for h in model.K);
    model.obj=pyo.Objective(expr=val,sense=pyo.maximize);
    solver=pyo.SolverFactory('gurobi',solve_io='python').solve(model,tee=False);            
    data=np.zeros((N,S,J,t_max))
    print(pyo.value(model.obj));
    for k in model.T:
          for i in model.I:
              for j in model.J:
                  for h in model.K:
                            data[i-1,j-1,h-1,k-1]=pyo.value(model.x[i,j,h,k]);
    return data
data = OptimalProblem()
listx=['黄豆','黑豆','红豆','绿豆','爬豆','小麦','玉米','谷子',	'高粱','黍子','荞麦','南瓜','红薯','莜麦','大麦','水稻','豇豆','刀豆','芸豆','土豆','西红柿','茄子','菠菜',' 	青椒','菜花'	,'包菜','油麦菜','小青菜','	黄瓜',	'生菜', 	'辣椒','	空心菜'	,'黄心菜',	'芹菜','	大白菜','	白萝卜',	'红萝卜'	,'榆黄菇',	'香菇',	'白灵菇','羊肚菌']
listy=[['A{}'.format(i) for i in range(1,7)],['B{}'.format(i) for i in range(1,15)],['C{}'.format(i) for i in range(1,7)],['D{}'.format(i) for i in range(1,9)],\
       ['E{}'.format(i) for i in range(1,17)],['F{}'.format(i) for i in range(1,5)]];

listy=list(chain(*listy));
def save_res(data):
    for t in range(0,t_max):
        datax=data[:,:,0,t];
        datax=datax.T;
        dat=pd.DataFrame(datax,columns=listx);
        dat['地块']=listy;
        dat.set_index('地块',inplace=True);
        
        datax=data[:,:,1,t];
        datax=datax.T;
        daty=pd.DataFrame(datax,columns=listx);
        daty['地块']=listy;
        daty.set_index('地块',inplace=True);
        
        
        with pd.ExcelWriter('result.xlsx',mode='a') as tf:
            #删除所有表单
            '''
            excel_file=pd.ExcelFile('result.xlsx');
            for x in  excel_file.sheet_names:
                 excel_file.parse(x).to_excel(tf,sheet_name=x,index=False);
            tf.save();
            '''
            dat.to_excel(tf,sheet_name='{}-第一季度'.format(2024+t));
            daty.to_excel(tf,sheet_name='{}-第二季度'.format(2024+t));
save_res(data);     