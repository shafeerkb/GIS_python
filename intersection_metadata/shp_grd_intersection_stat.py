#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 26 14:52:13 2020

@author: vassar
"""


import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
from shapely.geometry import shape
from shapely.ops import  transform
import fiona
from rtree import index
import pyproj
from functools import partial
from multiprocessing import Pool
import time

def grid2shp(grid_input_csv,output_folder):
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
    
    UUID_grid=pd.read_csv(grid_input_csv) #read 
    UUID_grid=UUID_grid.sort_values([ 'lon','lat'], ascending=[True, True])
    
    grid_lon=list(sorted(set(UUID_grid['lon'])))
    grid_lat=list(sorted(set(UUID_grid['lat'])))
    
    grid=np.array(UUID_grid['UUID']).reshape((len(grid_lon),len(grid_lat)))
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
    col.shape = (cols,1)    
    XXX=np.hstack((col,XXX))
    col=XX[:,-1]+DX[:,-1]
    col.shape = (cols,1) 
    XXX=np.hstack((XXX,col))
    #add edge Y   
    YYY=YY[:-1,:]+DY
    row=YY[0,:]-DY[0,:]
    row.shape = (1,rows)    
    YYY=np.vstack((row,YYY))
    row=YY[-1,:]+DY[-1,:]
    row.shape = (1,rows) 
    YYY=np.vstack((YYY,row))  
        
    
    polygons = []
    for x in range(cols):
        print(x,)
        for y in range(rows):
            
            xleft =float(XXX[y,x])
            xright=float(XXX[y,x+1])
                        
            ytop  =float(YYY[y,x])
            ybot  =float(YYY[y+1,x])
            
            polygons.append( Polygon([(xleft, ybot), (xright, ybot), (xright, ytop), (xleft, ytop)]) )
    uuid_df=pd.DataFrame(list(grid.flatten()),columns =['UUID'])
                                                      
    #Make UUID field
    grid_shp_uuid = gpd.GeoDataFrame(uuid_df, geometry=polygons)
    #add projection
    grid_shp_uuid.crs = {'init' :'epsg:4326'}
    grid_shp_uuid.to_file(output_folder+'/grid.shp')
    print("grid2shp  :",round(time.time() - start_time,2),"Sec")
#    return grid_shp_uuid
def get_area_km2(geometry):
    '''
        Parameters
    ----------
    geometry : Shaply geometry
        Intersection

    Returns
    -------
    TYPE
        Area in km2.

    '''
    shapely_geometry = shape(geometry)
    geom_aea = transform(
        partial(
            pyproj.transform,
            pyproj.Proj("+init=EPSG:4326"),
            pyproj.Proj(
                proj="aea",
                lat_1=shapely_geometry.bounds[1],
                lat_2=shapely_geometry.bounds[3],
            ),
        ),
        shapely_geometry,
    )
    return round(geom_aea.area/1000/1000,4) 


def f(polyg):
    '''
    
    Parameters
    ----------
    polyg : geometry.polygon
        Inut entity polygon

    Returns
    -------
    entity and associated_entity polygon inter section area 

    '''
    
    grid_cells1=fiona.open(grd_shp_file)
    a = []    #empty Dictnary
    poly = shape(polyg['geometry']).buffer(0)  #buffer(0) for used to “clean” self-touching or self-crossing polygons such as “bowtie”
    # Merge cells that have overlapping bounding boxes

    import warnings
    warnings.filterwarnings("ignore")
    
    for pos in idx.intersection(poly.bounds):

        try:
            intersection=poly.intersection(shape(grid_cells1[pos]['geometry']))
            if intersection.area > 0:
                    area_fract=intersection.area/shape(grid_cells1[pos]['geometry']).area
                    area_actual=get_area_km2(intersection)
                    prop = {'entity_uuid': polyg['properties']['UUID'],
                            'associated_entity_uuid' : grid_cells1[pos]['properties']['UUID'],
                            'intersection_area_km2':area_actual, 
                            'intersection_percentage': round(area_fract*100,3),                           
                            
                            }
                    a.append(prop)

        except Exception as e: 
                print(e)
                print(str(polyg['properties']['UUID'])+" , "+str(pos)+" , "+str(grid_cells[pos]['properties']))

#    print(polyg['properties']['OBJECTID_1'],7163,polyg['properties']['state'],polyg['properties']['district'],round(A_m1,2),round(A_m2,2))
#    print(polyg['properties']['OBJECTID'],102,polyg['properties']['SUB_BASIN'],round(A_m1,2),round(A_m2,2),(time.time() - start_time)/60)
    print(polyg['properties']['UUID'], "Elapsed time:",round((time.time() - start_time)/60,2),"Mint." )
    return a

if __name__ == '__main__':
    import sys
    
    ''' 
    First  arguments -->Input grid with input column(lon,lat,UUID)
    Second arguments -->Input shapefile wilth UUID 
    Third  arguments -->Output file name (csv)
    Fourth arguments -->No of processes for parellel
    Fifth  arguments -->Output folder
    
    python shp_grd_intersection_stat.py ="/home/vassar/SuBBasin_Intersection /IMD_0.027.csv" "/home/vassar/Block&&SubBasin/Block_UUID (1)/Block_GWR_new_geo_UUID.shp" 'grid_shp_metadata.csv' "4" "/home/vassar/shp_int/"
    '''    

    grid_input_csv=sys.argv[1]  
    in_shap_name= sys.argv[2]
    grid_shp_metadata = sys.argv[3]
    processes_no = int(sys.argv[4])
    output_folder = sys.argv[5]
    
#     grid_input_csv="/home/vassar/Documents/Rahul/SuBBasin_Intersection /IMD_0.027.csv"
# #    in_shap_name = '/home/vassar/Documents/Rahul/SuBBasin_Intersection /New_subbasin shapefile/SUBBASIN_CWC_UUID_JOIN_new.shp'
#     in_shap_name = "/home/vassar/Documents/Rahul/Block&&SubBasin/Block_UUID (1)/Block_GWR_new_geo_UUID.shp"
#     grid_shp_metadata = 'grid_shp_metadata.csv'
#     processes_no=int("4")
#     output_folder ="/home/vassar/shp_int/"
    
    grd_shp_file=output_folder+"/grid.shp"
    
    start_time = time.time() 
    
    grid2shp(grid_input_csv,output_folder) #create grid shapefile from csv
    
    grid_cells = fiona.open(grd_shp_file) #read Grid shapefile
    
    # Populate R-tree index with bounds of grid cells
    idx = index.Index()
    for pos, cell in enumerate(grid_cells):
        # assuming cell is a shapely object
        print(pos)
        idx.insert(pos, shape(cell['geometry']).bounds)
    
    start_time = time.time()
    #initialize multiprocessing pool
    p = Pool(processes=processes_no)  
    #calling multiprocessing pool
    result = p.map(f,fiona.open(in_shap_name))  
    
    df=pd.DataFrame(result[0])
    for i in range(1,len(result) ):
        df=df.append(pd.DataFrame(result[i]))
    
    df.to_csv(output_folder+grid_shp_metadata,index=False)  #Save output file
        