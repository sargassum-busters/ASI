#!/usr/bin/env python3
"""
Created on Thu Dec  5 12:47:06 2019
@author: urielm
"""

import pandas as pd
import geopandas as gpd
from osgeo import gdal

from glob import glob
from datetime import datetime
import os

def geotiffTogeojson(path_GeoTIFF, path_Geojson, path_Shapefile):
	"""Funcion que convierte el GeoTIFF binario de 0 y 1, en un formato vectorial GeoJson, con atributos de
	id, tiempo, area, fecha y tile

	Ejemplo:
	path_GeoTIFF = './data_GeoTIFF/'
	"""
	epoch = datetime.utcfromtimestamp(0)

	files = glob(path_GeoTIFF+'*.tif')
	files.sort()

	index = 0

	for file in files:

		tile = file.split('/')[-1].split('_')[0]
		timeS = file.split('/')[-1].split('_')[1]
		dateT = datetime.strptime(timeS,'%Y%m%dT%H%M%S')
		time = (dateT - epoch).total_seconds() * 1000.0

		print(tile)
		print(dateT.strftime('%Y-%m-%dT%H:%M:%SZ'))

		os.system('gdal_polygonize.py '+file+' '+path_Shapefile+tile+'_'+timeS+'_out.shp')

		df = gpd.read_file(path_Shapefile+tile+'_'+timeS+'_out.shp')

		df = df[df.DN == 1]

		if len(df)>= 1:

			df["area"] = round(df['geometry'].area,2)
			#dateT = datetime.strptime(timeS,'%Y%m%d')
			#time = (dateT - epoch).total_seconds() * 1000.0
			df['time'] = time
			#df['time'] = df['time'].astype('datetime64[ns]')

			df['fecha'] = dateT.strftime('%Y-%m-%dT%H:%M:%S.0Z')
			#df['fecha'] = df['fecha'].astype('datetime64[ns]')
			#df['fecha'] = pd.to_datetime(df['fecha'])

			df['tile'] = tile
			df['index'] = index
			df['IDpolygon'] = range(1, len(df) + 1)
			df.to_file(path_Geojson+"afai_"+tile+'_'+timeS+".json", driver="GeoJSON")

			index = index + 1

def multiGeojson(path_Geojson,multi_Geojson):
	""" Convierte todos los archivos GEojson, en uno solo con atributo temporal, compatible con el pluging de Leaflet
	TimeDimension el cual permite hacer animaciones.

	Ejemplo:
	path = './data_Geojson/20190706/'
	multi_Geojson = 'afai_T16QEJ_201907_multi.json'
	"""
	files_json = glob(path_Geojson+'*.json')
	files_json.sort()

	gdf_b = gpd.read_file(files_json[0])
	gdf_b = gdf_b.to_crs({'init': 'epsg:4326'})

	print ('Creando multijson ...')
	for json in files_json[1:]:

		gdf_i = gpd.read_file(json)

		gdf_i = gdf_i.to_crs({'init': 'epsg:4326'})

		gdf_b = pd.concat([gdf_b,gdf_i])

	#gdf_b = gdf_b.to_crs({'init': 'epsg:4326'})

	gdf_b.to_file(multi_Geojson, driver="GeoJSON")

def jsVariable(multi_geojson,variable_js):
	""" Convierte los datos Geojson y los convierte en una variable JavaScript, necesaria para la lectura
	del modulo de Lealfet TimeDimension.

	Ejemplo:
	geojson = 'afai_T16QEJ_201907_multi.json'
	variable_js = 'afai_T16QEJ_201907_multi.js'
	"""
	multi_json = open(multi_geojson,'r')
	data_json = multi_json.read()
	data_js = 'var asi = '+ data_json
	multi_js = open(variable_js,'w')

	multi_js.write(data_js)
	multi_js.close()
	multi_json.close()

def geojsonShapefile(multi_geojson):
	""" Convierte un archivo geojson en un shapefile.

	Ejemplo:
	geojson = 'afai_T16QEJ_201907_multi.json'
	"""
	#file_multi = glob('./data_multiGeojson/*.json')

	df = gpd.read_file(multi_geojson)
	df.to_file("data_multiShapefile/afai_multi.shp", driver="ESRI Shapefile")

path_TarGZ = './data_TarGZ/*'

for file in glob(path_TarGZ):

	print(file)
	dia = file.split('/')[-1].split('.')[0]
	print(dia)

	path_GeoTIFF = './data_GeoTIFF/'+dia+'/'
	path_Shapefile = './data_Shapefile/'+dia+'/'
	path_Geojson = './data_Geojson/'+dia+'/'
	multi_Geojson = 'multi_Geojson.json'

	geotiffTogeojson(path_GeoTIFF,path_Geojson,path_Shapefile)

variable_js = 'animacion.js'
multiGeojson(path_Geojson,multi_Geojson)
jsVariable(multi_Geojson,variable_js)
#geojsonShapefile(multi_Geojson)
