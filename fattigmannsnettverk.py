# -*- coding: utf-8 -*-
"""
Created on Fri Aug 25 13:05:29 2017

@author: jajens
"""



import json
import pyproj
import ruteplan
import geopandas as gpd
import pdb

wgs84 = pyproj.Proj(init='EPSG:4326')
utm33 = pyproj.Proj(init='EPSG:25833')


mycollection = {
                    "type": "FeatureCollection",
                    "crs": {
                        "type": "name",
                        "properties": {
                            "name": "urn:ogc:def:crs:EPSG::25833"
                        }
                    },
                    "features": []
                }
                        
                        

with open( 'noder-tilvegvesen.json') as f:
    punktdata = json.load( f) 



maal = (191809.5, 6678340.1)

nyepunkt = []
for kk, punkt in enumerate( punktdata['resultat']) : 
    x, y = pyproj.transform( wgs84, utm33, 
                            punkt['googlesvar'][0]['geometry']['location']['lng'], 
                            punkt['googlesvar'][0]['geometry']['location']['lat'])
    punkt['posisjon'] = (x, y)
    print( 'Henter', punkt['minadr'] )

    try: 
        r = ruteplan.anropruteplan( coordinates=[ punkt['posisjon'], maal], 
            server='ruteplanTriona', ruteplanparams={ 'format' :  'json', 
            'route_type' : 'alternative', 'geometryformat' : 'iso' })

        nyedata = ruteplan.parseruteplan( r, egenskaper=punkt, startvertices=20)
                                
    except ValueError as e:
        z = e
        print( z)
        print( 'Nr', str(kk), 'FEILER', punkt )
    else:                           
        for data in nyedata: 
            if data['properties']['rutealternativNr'] == 0:
                nyepunkt.append(data)
            
    finally: 
        pass
    

mycollection['features'] = nyepunkt


with open( 'testruter-geojson-25833.json', 'w') as f:
    json.dump( mycollection, f)
    
    
# Konverterer til lat-lon via geopandas
gdf = gpd.GeoDataFrame.from_features(  mycollection['features']) 
gdf.crs = { 'init' : 'epsg:25833' }
nygdf = gdf.to_crs( epsg=4326) 

nygdf_as_str = nygdf.to_json()

with open( 'testruter-geojson-4326.json', 'w') as f:
    json.dump( nygdf_as_str, f)



