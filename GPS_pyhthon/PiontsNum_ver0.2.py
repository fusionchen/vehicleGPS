# -*- coding: utf-8 -*-
"""
Created on Fri Sep  8 11:14:58 2017

@author: Zhwh-notbook
"""
import pandas as pd
import math
import numpy as np
#==============================================================================
# 根据经纬度计算两点见距离的函数
#==============================================================================
def calcDistance(Lat_A, Lng_A, Lat_B, Lng_B):
    ra = 6378.140  # 赤道半径 (km)
    rb = 6356.755  # 极半径 (km)
    flatten = (ra - rb) / ra  # 地球扁率
    rad_lat_A = math.radians(Lat_A)
    rad_lng_A = math.radians(Lng_A)
    rad_lat_B = math.radians(Lat_B)
    rad_lng_B = math.radians(Lng_B)
    pA = math.atan(rb / ra * math.tan(rad_lat_A))
    pB = math.atan(rb / ra * math.tan(rad_lat_B))
    ss = math.sin(pA) * math.sin(pB) + math.cos(pA) * math.cos(pB) * math.cos(rad_lng_A - rad_lng_B)
    if ss>1:
        ss = 1
    if ss<-1:
        ss = -1    
    xx = math.acos(ss)
    c1 = (math.sin(xx) - xx) * (math.sin(pA) + math.sin(pB)) ** 2 / math.cos(xx / 2) ** 2
    if math.sin(xx/2) == 0:
        c2 = 0
    else:
        c2 = (math.sin(xx) + xx) * (math.sin(pA) - math.sin(pB)) ** 2 /\
        math.sin(xx/2) ** 2
    dr = flatten/8 * (c1 - c2)
    distance = ra * (xx + dr)
    return (distance)
# =============================================================================
# 给定范围内的异常点的数量计算:
'''
1. 计算输入数据框中相对固定里程道路区间内的坐标点数量
'''
# =============================================================================
def Numcoordinate(GPSData,L=100):
    #GPSData = GPSData.sort_values(by=['longitude','latitude'],ascending=True)
    GPSData = GPSData.sort_values(by=['GpsTime'],ascending=True)
    GPSData['spacing'] = 0
    # 重新计算相邻点之间的距离
    for i in range(len(GPSData.index)):
         if i==0:
             GPSData['spacing'].values[i] = 0
         else:
             k = i-1
             Lat_A = GPSData['latitude'].iloc[k]
             Lng_A = GPSData['longitude'].iloc[k]
             Lat_B = GPSData['latitude'].iloc[i]
             Lng_B = GPSData['longitude'].iloc[i]
             GPSData['spacing'].values[i] = calcDistance(Lat_A, Lng_A, Lat_B, Lng_B)*1000
    #计算距离第一点的行驶距离
    GPSData['distance'] = 0
    for i in range(len(GPSData.index)):
         if i==0:
             GPSData['distance'].values[i] = 0
         else:
             temp = GPSData['distance'].iloc[i-1]
             GPSData['distance'].values[i] = temp + GPSData['spacing'].iloc[i]
    '''
    增加secction列，用于描述每行数据所属的道路路段编号
    1. 以第一行数据开始，逐行比较与第一行点的里程距离，如果n行数据距离大于L，则0-（n-1）为第一路段
    2. 以第n行为起点计算下一个距离大于L的数据行
    3. 以此类推
    ''' 
    secctionNum = math.floor(max(GPSData['distance'])/L)+1
    colnames = ["sectionID","BPlongitude","BPlatitude","EPlongitude","EPlatitude","distance","pointNum"]
    Numpoints = pd.DataFrame(index=np.arange(0,secctionNum),columns=colnames)
    
    for i in range(len(Numpoints.index)):
        BP = L*i
        EP = L*(i+1)
        a = GPSData.loc[(GPSData['distance'] >= BP) & (GPSData['distance'] <= EP)].copy()
        num = len(a.index)-1
        Numpoints["sectionID"].values[i] = i
        
        if len(a.index) == 0:
            print('i=',i)
            #Numpoints["BPlongitude"].values[i] = a['longitude'].iloc[0]
            #Numpoints["BPlatitude"].values[i] = a['latitude'].iloc[0]
            #Numpoints["EPlongitude"].values[i] = a['longitude'].iloc[num]
            #Numpoints["EPlatitude"].values[i] = a['latitude'].iloc[num]
            Numpoints["pointNum"].values[i] = 0
            #Numpoints["distance"].values[i] = 0
        
        if len(a.index) > 0:
            print('i=',i)
            Numpoints["BPlongitude"].values[i] = a['longitude'].iloc[0]
            Numpoints["BPlatitude"].values[i] = a['latitude'].iloc[0]
            Numpoints["EPlongitude"].values[i] = a['longitude'].iloc[num]
            Numpoints["EPlatitude"].values[i] = a['latitude'].iloc[num]
            Numpoints["pointNum"].values[i] = len(a.index)
            #Numpoints["distance"].values[i] = sum(a['spacing'])
    
    Numpoints = Numpoints.loc[(Numpoints["pointNum"] != 0) ].copy()   
        
    for i in range(len(Numpoints.index)):
        #if i > 0:
            #Numpoints["BPlongitude"].values[i] = Numpoints["EPlongitude"].iloc[i-1]
            #Numpoints["BPlatitude"].values[i] = Numpoints["EPlatitude"].iloc[i-1]
          
        Lat_A = Numpoints["BPlatitude"].iloc[i]
        Lng_A = Numpoints["BPlongitude"].iloc[i]
        Lat_B = Numpoints["EPlatitude"].iloc[i]
        Lng_B = Numpoints["EPlongitude"].iloc[i]
        Numpoints["distance"].values[i] = calcDistance(Lat_A, Lng_A, Lat_B, Lng_B)*1000
        
    Numpoints["Num_per_m"] = Numpoints["pointNum"]/Numpoints["distance"]
    return (Numpoints)
        
'''
目前存在的问题是：
1. 没有数据行的里程区间被直接加入后续里程编号，如200-300区间没有有效数据，则后续300-400区间被直接
    扩充为200-400区间，降低了路段相对集中程度
'''        

# =============================================================================
# 直接根据与相邻点的距离进行聚类
'''
计算输入数据框每行数据与前后数据行的距离
根据距离对某行坐标是否为独立事件点进行聚类分析
聚类结果标识在cluster数据列
函数中：
L：分段的长度，间距大于该分段长度的为独立点
Nclusters： 聚类预设的分类数量
'''          
# =============================================================================
            
def IndependentPoint(map_ab,L=300,Nclusters=2):
    map_ab = map_ab.sort_values(by=['vehicleID','GpsTime'],ascending=True)
    map_ab['spacing_front'] = 0    # 重新计算相邻点之间的距离
    for i in range(len(map_ab.index)):
         if i==0:
             map_ab['spacing_front'].values[i] = 0
         else:
             k = i-1
             Lat_A = map_ab['latitude'].iloc[k]
             Lng_A = map_ab['longitude'].iloc[k]
             Lat_B = map_ab['latitude'].iloc[i]
             Lng_B = map_ab['longitude'].iloc[i]
             map_ab['spacing_front'].values[i] = calcDistance(Lat_A, Lng_A, Lat_B, Lng_B)*1000
             
    map_ab['spacing_behind'] = 0    # 重新计算相邻点之间的距离
    for i in range(len(map_ab.index)):
         if i==(len(map_ab.index)-1):
             map_ab['spacing_behind'].values[i] = 0
         else:
             k = i+1
             Lat_A = map_ab['latitude'].iloc[k]
             Lng_A = map_ab['longitude'].iloc[k]
             Lat_B = map_ab['latitude'].iloc[i]
             Lng_B = map_ab['longitude'].iloc[i]
             map_ab['spacing_behind'].values[i] = calcDistance(Lat_A, Lng_A, Lat_B, Lng_B)*1000
    
    
    from sklearn.cluster import KMeans
    #import matplotlib.pyplot as plt 
    #X = 1.0*(map_ab['spacing']-map_ab['spacing'].mean())/map_ab['spacing'].std()
    a = map_ab.loc[(map_ab['spacing_front'] > L) & (map_ab['spacing_behind'] > L)].copy()
    map_ab = map_ab.loc[(map_ab['spacing_front'] <= L) & (map_ab['spacing_behind'] <= L)]
    X = map_ab[['spacing_front','spacing_behind']]
    
    #X = [[i] for i in X]
    #X = np.array(X).tolist()
    #Nclusters = 2
    iteration = 5000
    kmeanModel = KMeans(n_clusters = Nclusters ,n_jobs = 4,max_iter = iteration)    
    y_pred = kmeanModel.fit(X)
    map_ab['cluster'] = y_pred.labels_
    a['cluster'] = 1
    map_ab = pd.concat([map_ab,a],ignore_index=True)
    map_ab = map_ab.sort_values(by=['vehicleID','GpsTime'],ascending=True)
    #plt.scatter(X.ix[:, 0], X.ix[:, 1], c=X.ix[:, 2])
    #plt.show()
    return (map_ab)