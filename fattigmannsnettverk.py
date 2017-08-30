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
import csv

def lonlat2utm33( lon, lat):
    """Reprojiserer lon/lat til X-Y i UTM33 epsg25833. Returnerer en tuple med (X,Y)
    """

    wgs84 = pyproj.Proj(init='EPSG:4326')
    utm33 = pyproj.Proj(init='EPSG:25833')
    
    x, y = pyproj.transform( wgs84, utm33, lon, lat)
    return (x,y)


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

    # Henter UTM33 koordinater
    punkt['posisjon'] = lonlat2utm33( 
            punkt['googlesvar'][0]['geometry']['location']['lng'],  
            punkt['googlesvar'][0]['geometry']['location']['lat'] )
    
    print( 'Henter', punkt['minadr'] )

    try: 
        r = ruteplan.anropruteplan( coordinates=[ punkt['posisjon'], maal], 
            server='ruteplanTest', ruteplanparams={ 'format' :  'json', 
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
nygdf_as_json = json.loads( nygdf_as_str) 

with open( 'testruter-geojson-4326.json', 'w') as f:
    json.dump( nygdf_as_json, f)


### Itererer over alle mulige permutasjoner: 
    
# Lager subsett av data, for utviking 
del punktdata['resultat'][5:]

# Definerer datastruktur for CSV
mittsvar = { 'fra_nodeid' :  'text', 
            'til_nodeid' :  'text', 
            "Total_Meters" : 0,
            "Total_Minutes": 0,
            "Total_Toll large": 0,
            "Total_Toll small": 0,
            "FerryCount": 0,
            "TollCount": 0,
            "MeterFerry": 0,
            "routeName": "text",
            "totalRuteAltN": 0, 
            "filnavn" : "text"}
            

## Lagrer data for fattigmanns--nettverksanalyse
sammendragfil = 'alleruteforslag.csv'
outputdir = 'ruteforslag/'

f = open( sammendragfil, 'w')
w = csv.DictWriter(f, mittsvar.keys(), delimiter=";", 
                  quoting=csv.QUOTE_ALL, lineterminator='\n')
w.writeheader()

for i1, p1 in enumerate( punktdata['resultat']): 
    
    print( 'Iterasjon ', str(i1), p1['nodeid'] )
    
    # Trenger du kun den ene retningen? A->B, men ikke motsatt?
    # for i2, p2 in enumerate( punktdata['resultat'][i1:]):

    # BEGGE retninger, A->B og B->A
    for i2, p2 in enumerate( punktdata['resultat']): 
        
        if p1['nodeid'] != p2['nodeid']: 
            
            
            mittsvar['fra_nodeid'] = p1['nodeid']
            mittsvar['til_nodeid'] = p2['nodeid']
            mittsvar['filnavn'] = outputdir + 'rute' + mittsvar['fra_nodeid'] \
                    + '_' + mittsvar['til_nodeid'] + '.geojson'
     
            # Henter ruteplandata
            try: 
                r = ruteplan.anropruteplan( coordinates=[ p1['posisjon'], 
                                                         p2['posisjon']], 
                    server='ruteplanTEST', ruteplanparams={ 'format' :  'json', 
                    'route_type' : 'alternative', 'geometryformat' : 'iso' })
        
                egenskaper = { 'fra_nodeid' : mittsvar['fra_nodeid'], 
                                'til_nodeid' : mittsvar['til_nodeid'] }
                rutedata = ruteplan.parseruteplan( r, egenskaper=egenskaper)
                                        
            except ValueError as e:
                z = e
                print( z)
                print( 'Ruteberegning FEILER', mittsvar['fra_node'], ' -> ', mittsvar['til_node'])
                
                mittsvar['Total_Meters'] = None
                mittsvar['Total_Minutes'] = None
                mittsvar['Total_Toll_small'] = None
                mittsvar['Total_Toll_large'] = None
                mittsvar['FerryCount'] = None
                mittsvar['TollCount'] = None
                mittsvar['MeterFerry'] = None
                mittsvar['routeName'] = 'FEILER'
                mittsvar['routeName'] = 'FEILER'
                mittsvar['totalRuteAltN'] = None
                
            else:                           
                
                mittsvar['Total_Meters'] = rutedata[0]['properties']['Total_Meters']
                mittsvar['Total_Minutes'] = rutedata[0]['properties']['Total_Minutes']
                mittsvar['Total_Toll_small'] = rutedata[0]['properties']['Total_Toll small']
                mittsvar['Total_Toll_large'] = rutedata[0]['properties']['Total_Toll large']
                mittsvar['FerryCount'] = rutedata[0]['properties']['FerryCount']
                mittsvar['TollCount'] = rutedata[0]['properties']['TollCount']
                mittsvar['MeterFerry'] = rutedata[0]['properties']['MeterFerry']
                mittsvar['routeName'] = rutedata[0]['properties']['routeName']
                mittsvar['routeName'] = rutedata[0]['properties']['routeName']
                mittsvar['totalRuteAltN'] = len(rutedata)
                
                
                # Konverterer til lat-lon via geopandas, skriver geojson
                gdf = gpd.GeoDataFrame.from_features( rutedata ) 
                gdf.crs = { 'init' : 'epsg:25833' }
                nygdf = gdf.to_crs( epsg=4326) 
                
                nygdf_as_str = nygdf.to_json()
                nygdf_as_json = json.loads( nygdf_as_str) 
                
                with open( mittsvar['filnavn'], 'w') as f2:
                    json.dump( nygdf_as_json, f2)
                
                
                
            finally: 
                pass         
                    
            
            
            w.writerow( mittsvar)
            

f.close()
