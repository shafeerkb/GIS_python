#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  3 07:15:07 2020

@author: vassar
"""
import geopandas as gp
import pandas as pd
import numpy as np
from shapely.geometry import Polygon


def progressBar(current, total, barLength = 50):
    percent = float(current) * 100 / total
    arrow   = '-' * int(percent/100 * barLength - 1) + '>'
    spaces  = ' ' * (barLength - len(arrow))

    print('Progress: [%s%s] %d %%' % (arrow, spaces, percent), end='\r')
    
def grid2shp(grid_input_csv):
    '''
    Function to create grid to shapefile polygons
    Parameters
    ----------
    grid_input_csv : String
        Input file in csv with lon,lat,UUID column.
    output_folder : String
        Output file location.

    Returns
    -------
    grid_shp_uuid : geopandas GeoDataFrame
    
    '''
    print("creating grid polygons")
    
    UUID_grid=pd.read_csv(grid_input_csv) #read 
    UUID_grid=UUID_grid.sort_values([ 'lon','lat'], ascending=[True, True])
    
    grid_lon=list(sorted(set(UUID_grid['lon'])))
    grid_lat=list(sorted(set(UUID_grid['lat'])))
    
#    grid=np.array(UUID_grid['UUID']).reshape((len(grid_lon),len(grid_lat)))
    XX, YY = np.meshgrid(grid_lon, grid_lat)
    
    # CALCULATE DIFF
    DX = np.diff(XX,axis=1)/2
    DY = np.diff(YY,axis=0)/2
    # get rows
    rows = YY.shape[0]
    # get columns
    cols = XX.shape[1]
     
    #add edge X
    XXX=XX[:,:-1]+DX
    col=XX[:,0]-DX[:,0]
    col.shape = (rows,1)    
    XXX=np.hstack((col,XXX))
    col=XX[:,-1]+DX[:,-1]
    col.shape = (rows,1) 
    XXX=np.hstack((XXX,col))
    #add edge Y   
    YYY=YY[:-1,:]+DY
    row=YY[0,:]-DY[0,:]
    row.shape = (1,cols)    
    YYY=np.vstack((row,YYY))
    row=YY[-1,:]+DY[-1,:]
    row.shape = (1,cols) 
    YYY=np.vstack((YYY,row))  
        
    
    polygons = []
    for x in range(cols):
        progressBar(x+1,cols)
        for y in range(rows):
            
            xleft =float(XXX[y,x])
            xright=float(XXX[y,x+1])
                        
            ytop  =float(YYY[y,x])
            ybot  =float(YYY[y+1,x])
            if(np.any((UUID_grid["lon"]==XX[y,x])&(  UUID_grid["lat"]==YY[y,x]))):
                polygons.append( Polygon([(xleft, ybot), (xright, ybot), (xright, ytop), (xleft, ytop)]) )  
                
    #Make UUID field
    grid_shp_uuid = gp.GeoDataFrame(UUID_grid['UUID'], geometry=polygons)
    #add projection
    grid_shp_uuid.crs = {'init' :'epsg:4326'}
#    grid_shp_uuid.to_file(output_folder+'/grid.shp')
    return grid_shp_uuid

def Polygon_inter(poly1,uuid_1,poly2,uuid_2):
    '''

    Parameters
    ----------
    poly1 : geopandas.geodataframe.GeoDataFrame
        First polygon.
    uuid_1 : String
        Column name in poly1
    poly2 : geopandas.geodataframe.GeoDataFrame
        Second polygon.
    uuid_2 : String
        Column name in poly2.

    Returns
    -------
    geopandas.geodataframe
        Intersection .

    '''
    
    poly1["Area1"]=poly1.area
    
    poly1["Area2"]=poly2.area
    
    inter = gp.overlay(poly1, poly2, how='intersection')
    
    #inter.to_file("intersection_poly.shp")
    
    inter["Area_int"]=inter.area
    
    inter_csv=inter[[uuid_1,uuid_2,'Area1','Area2','Area_int']]
    inter_csv["percent_1"]=round(inter_csv["Area_int"]/inter_csv["Area1"]*100,4)
    inter_csv["percent_2"]=round(inter_csv["Area_int"]/inter_csv["Area2"]*100,4)
    return inter_csv[[uuid_1, uuid_2,'percent_1', 'percent_2']]
#    (inter_csv[[uuid_1, uuid_2,'percent_1', 'percent_2']]).to_csv("test.csv")
    
if __name__ == '__main__':
    
    '''
    First  arguments -->Input shapefile/grid with input column(lon,lat,UUID)
    Second arguments -->Column Name
    Third  arguments -->Input shapefile/grid with input column(lon,lat,UUID)
    Fourth arguments -->Column Name
    Fifth  arguments -->Output file name (csv)
    
    python intersection_stat.py "/home/vassar/IMD_0.25_India_grids_only.shp" "grid_ud" "/home/vassar/nrscdata_0.05.csv" "UUID" "intersction_metadata.csv"
    
    '''   
    import sys
    import time
    import warnings
    warnings.filterwarnings("ignore")
    start_time = time.time() 

    
    f1_fname=sys.argv[1]  
    uuid_1= sys.argv[2]
    f2_fname = sys.argv[3]
    uuid_2 = sys.argv[4]
    output_file = sys.argv[5]
    
    # f1_fname="/home/vassar/new_inter/IMD_0.25/IMD_0.25_India_grids_only.shp"
    # f2_fname="/home/vassar/Downloads/nrscdata_0.05.csv"#"/home/vassar/new_inter/grid.shp"
    # uuid_1="grid_ud"
    # uuid_2="UUID"
    # output_file="intersction_metadata.csv"
    
    try:
        
        if(f1_fname.lower().endswith(('.shp'))):
            poly1=gp.read_file(f1_fname)
        elif(f1_fname.lower().endswith(('.csv'))):
            poly1=grid2shp(f1_fname)
        else:
            print("Invalid file :", f1_fname)
            raise Exception 
            
        if(any(poly1.columns==uuid_1)==False):
            print(uuid_1,"column not found!")
            raise Exception 
            
        if(f2_fname.lower().endswith(('.shp'))):
            poly2=gp.read_file(f2_fname)
        elif(f2_fname.lower().endswith(('.csv'))):
            poly2=grid2shp(f2_fname)
        else:
            print("Invalid file :", f2_fname)  
            raise Exception 
            
        if(any(poly2.columns==uuid_2)==False):
            print(uuid_2,"column not found!")
            raise Exception 
    
        int_csv=Polygon_inter(poly1,uuid_1,poly2,uuid_2)      
        int_csv.to_csv(output_file,index=False)
        print("\n Done!  :",round(time.time() - start_time,2),"Sec")
    except Exception as e: 
        print(e)
        
        