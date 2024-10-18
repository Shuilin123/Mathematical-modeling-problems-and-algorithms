# -*- coding: utf-8 -*-
import pickle
import numpy as np
import pandas as pd
# 读入原始数据
data1=pd.read_excel('../附件1.xlsx',sheet_name='乡村的现有耕地');
data2=pd.read_excel('../附件1.xlsx',sheet_name='乡村种植的农作物');
data3=pd.read_excel('../附件2.xlsx',sheet_name='2023年的农作物种植情况');
datax=data1.loc[:,['地块类型','地块名称']];
datay=data2.loc[:,['作物名称','作物类型']];
datay=datay.iloc[0:41,:];
data3=pd.merge(datax,data3,left_on='地块名称',right_on='地块名称',how='inner');
data4=pd.read_excel('../附件2.xlsx',sheet_name='2023年统计的相关数据');
## 定义基本参数
N=41;#粮食种类
M=100000;
J=2;#季度数
block_counts = {
    '平旱地': 6,
    '梯田': 14,
    '山坡地': 6,
    '水浇地': 8,
    '普通大棚': 16,
    '智慧大棚': 4
}
# 地块数
S = sum(block_counts.values())
block_types = list(block_counts.keys())

block_sets = {
    block_type: set(range(sum(block_counts[bt] for bt in block_types[:i]), sum(block_counts[bt] for bt in block_types[:i+1])))
    for i, block_type in enumerate(block_types)
}
#价格
c=np.zeros((N,S,J));
#成本
q=np.zeros((N,S,J));
#需求
d=np.zeros((N,S,J));
dmand=M*np.ones((N,S,J));
##定义地块类型集合
#计算价格和成本表格
#41种作物
#(2) 智慧大棚第一季可种植的蔬菜作物及其亩产量、种植成本和销售价格均与普通大棚相同，表中省略。
val=pd.DataFrame();
val2=pd.DataFrame();
data4=data4.iloc[0:107,:];
def process_price(x):
    dat=x['销售单价/(元/斤)'];
    if not isinstance(dat,str):
        dat=dat.astype(str);
        dat=dat.str.split('-');
        datx=dat.tolist();
        dat=np.array(datx);
    else:
        dat=dat.split('-');
        dat=np.array(dat);
    dat=dat.astype(float);
    return dat
for i in range(0,len(data4)):
    dat=data4.iloc[i,:];
    if dat['地块类型']=='智慧大棚':
        #确定作物
        cond1=data4['作物编号']==dat['作物编号'];
        #确定季次
        cond2=data4['种植季次']=='第一季';
        #确定地块类型
        cond3=data4['地块类型']=='智慧大棚';
        #获取对应行
        val1=data4.loc[cond1&cond2&cond3,:];
        if len(val1)==0:
            cond3=data4['地块类型']=='普通大棚 ';
            val1=data4.loc[cond1&cond2&cond3,:];
            datx=process_price(val1);
            datx=datx.reshape(1,-1);
            valx=pd.DataFrame(datx,columns=['low','High'])
            val2=pd.concat([val2,valx], ignore_index=True) 
            val= pd.concat([val,val1], ignore_index=True)
    else:
        datx=process_price(dat);
        datx=datx.reshape(1,-1);
        valx=pd.DataFrame(datx,columns=['low','High'])
        val2=pd.concat([val2,valx], ignore_index=True)
val['地块类型']='智慧大棚';
data4=pd.concat([data4,val]);
data4[['low','High']]=val2;
for i in range(1,N+1):
    cond1=data4['作物编号']==i;
    datx=data4.loc[cond1,:];
    i=i-1;
    for cnt in range(len(datx)):
        dat=datx.iloc[cnt];
        crop_season=dat['种植季次'];
        area_name=dat['地块类型'];
        for val in block_types:
            if area_name==val:
                for j in block_sets[val]:
                    if crop_season=='单季' or crop_season=='第一季':
                        k=0;
                    else:
                        k=1;
                    c[i,j,k]=(dat['low']+dat['High'])/2;
                    q[i,j,k]=dat['种植成本/(元/亩)'];
                    d[i,j,k]=dat['亩产量/斤'];
    cond1=data3['作物编号']==i;
    cond2=data4['作物编号']==i;
    datx=data3.loc[cond1,:];
    daty=data4.loc[cond2,:];
    i=i-1;
    for cnt in range(len(datx)):
        dat=datx.iloc[cnt];
        crop_season=dat['种植季次'];
        area_name=dat['地块类型'];
        cond1=daty['种植季次']==crop_season;
        cond2=daty['地块类型']==area_name;
        datz=daty.loc[cond1&cond2,:];
        for val in block_types:
           if area_name==val:
               for j in block_sets[val]:
                    if crop_season=='单季' or crop_season=='第一季':
                        k=0;
                    else:
                        k=1;
                    dmand[i,j,k]=dat['种植面积/亩']*datz['亩产量/斤'].values[0];
with open("c.pkl",'wb') as tf:
    pickle.dump(c,tf);
with open("d.pkl",'wb') as tf:
    pickle.dump(d,tf);
with open("q.pkl",'wb') as tf:
    pickle.dump(q,tf);
with open("dmand.pkl",'wb') as tf:
    pickle.dump(dmand,tf);

