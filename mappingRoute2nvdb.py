import sys
import requests 
import json 

import pandas as pd
import geopandas as gpd
from shapely import wkt 
import numpy as np 

import ruteplan

# Importing the NVDB library  https://github.com/LtGlahn/nvdbapi-V3, 
# supposedly downloaded to your file system
# Alternatively you could run pip install  https://pypi.org/project/nvdbapi-v3/ 
if not [ k for k in sys.path if 'nvdbapi' in k]:
    print( "Adding NVDB api library to python search path")
    sys.path.append( '/mnt/c/data/leveranser/nvdbapi-V3' )
import nvdbapiv3 


if __name__ == '__main__': 
    p1 =  wkt.loads( 'POINT(262819.18 6649657.89 )' ) # Storgata 51, Oslo 
    p2 =  wkt.loads( 'POINT(260805.98 6649240.36 )' ) # Munkedamsveien 59, Oslo

    # Saving the JSON response for documentation 
    response =  ruteplan.anropruteplan( coordinates = [(p1.x, p1.y), (p2.x, p2.y) ]  )
    with open( 'ruteplanrespons.json', 'w') as f: 
        json.dump( response.json(), f, indent=4, ensure_ascii=False )

    routingdata = pd.DataFrame( ruteplan.ruteplan2dict( coordinates = [(p1.x, p1.y), (p2.x, p2.y) ]  ))

    # Extracting NVDB linear positions @ link sequence from ruteplan data
    # (which is list of list, hence the somewhat obscure code for list comprehension 
    # to flatten list of list => single list 
    temp = routingdata['nvdbreferences'].to_list()
    temp  = [ x for sublist in temp for x in sublist ] # Flattening with list comprehension

    # Rounding to 8 decimals precision for the linear positions 
    ruteplan_nvdblinks = []
    for linkref in temp: 
        linkref['fromrellen'] = round( linkref['fromrellen'], 8)
        linkref['torellen'] = round( linkref['torellen'], 8)
        ruteplan_nvdblinks.append( linkref )

    ruteplan_nvdblinksDF = pd.DataFrame( ruteplan_nvdblinks )

    # Now grabbing the NVDB link sequences that is referenced in the ruteplan data 
    # Iterating over the roadlink ID and flattening the data structure of /vegnett/veglenkesekvenser/segmentert
    # into a neat, flat dictionary (and ignoring some administrative info) 
    # Example https://nvdbapiles-v3.atlas.vegvesen.no/vegnett/veglenkesekvenser/segmentert/319528.json 
    NVDBroadlinklist = [] 
    headers =  { 'accept' : 'application/vnd.vegvesen.nvdb-v3-rev2+json',
                            'X-Client' : 'nvdbapi.py',
                            'X-Kontaktperson' : 'jan.kristian.jensen@vegvesen.no'}
    url = 'https://nvdbapiles-v3.atlas.vegvesen.no/vegnett/veglenkesekvenser/'
    for veglenkesekvensID in ruteplan_nvdblinksDF['reflinkoid'].unique(): 
        r = requests.get( url + str(veglenkesekvensID), headers=headers )
        if r.ok: 
            tmp = r.json()
            for lenke in tmp['veglenker']: 
                lenke['veglenkesekvensid'] = veglenkesekvensID
                if 'superstedfesting' in lenke: 
                    lenke['super_veglenkesekvensid'] = lenke['superstedfesting']['veglenkesekvensid']
                    lenke['super_startposisjon']     = lenke['superstedfesting']['startposisjon']
                    lenke['super_sluttposisjon']     = lenke['superstedfesting']['sluttposisjon']
                    lenke['super_retning']           = lenke['superstedfesting']['retning']
                    lenke['super_felt']           =  ','.join( lenke['superstedfesting']['kjørefelt'] )
                NVDBroadlinklist.append( nvdbapiv3.flatutvegnettsegment( lenke )  )

        else: 
            print( f"Can't fetch road link ID {veglenkesekvensID} HTTP status={r.status_code} message={ ' '.join(  r.text.split() )[:200]}")

    NVDBroadlinkDF = pd.DataFrame( NVDBroadlinklist)

    # List of "kjørebane" road link sequences, i.e. those link sequence at "Kjørebane" topology that must be mapped
    # to the "Vegtrasé" topology level    
    kjbn_topology = list( NVDBroadlinkDF[ ~NVDBroadlinkDF['superstedfesting'].isnull() ]['veglenkesekvensid'].unique())

    # Now we're ready to iterate over the NVDB road links in the ruteplan data set, 
    # constructing a mapping from kjørebane => Vegtrasé topology level where appropriate

    mapped_NVDBroadlinklist = []
    junk = []
    for linkref in ruteplan_nvdblinks: 

        if linkref['reflinkoid'] not in kjbn_topology:
            # No mapping nescessary, this link sequence is at the VT topology level 
            mapped_NVDBroadlinklist.append( linkref )

        else: 
            # Maping from kjørebane => vegtrasé using superstedfesting
            newlinkref = { 'kjbane' : linkref  }
            tempDF = NVDBroadlinkDF[ NVDBroadlinkDF['veglenkesekvensid'] == linkref['reflinkoid']]
            newlinkref['reflinkoid'] = tempDF.iloc[0]['super_veglenkesekvensid']

            # First check if linkref.fromrellen is an exact match for the startposisjon / sluttposisjon columns
            if len( tempDF[ tempDF['startposisjon'] == linkref['fromrellen'] ] == 1 ):
                newlinkref['fromrellen'] = tempDF[ tempDF['startposisjon'] == linkref['fromrellen'] ].iloc[0]['super_startposisjon']
            elif len( tempDF[ tempDF['sluttposisjon'] == linkref['fromrellen'] ] == 1 ):
                newlinkref['fromrellen'] = tempDF[ tempDF['sluttposisjon'] == linkref['fromrellen'] ].iloc[0]['super_sluttposisjon']
            else: 
                # Doesn't match start/end points exactly, we must interpolate
                temp2DF = tempDF[ (tempDF['startposisjon'] <= linkref['fromrellen']) & (linkref['fromrellen'] <=  tempDF['sluttposisjon'] ) ]
                if len( temp2DF ) != 1: 
                    print( f"WARNING - there should exactly one row matching position {linkref['fromrellen']} @ link sequence {linkref['reflinkoid']}, found {len(temp2DF)} ")
                newlinkref['fromrellen'] = round( np.interp( linkref['fromrellen'], 
                                                            [ temp2DF.iloc[0]['startposisjon'], temp2DF.iloc[0]['sluttposisjon'] ], 
                                                            [ temp2DF.iloc[0]['super_startposisjon'], temp2DF.iloc[0]['super_sluttposisjon'] ]  ), 8)                
                print( f"Interpolating fromrellen-position {linkref['fromrellen']} @ {linkref['reflinkoid']} => {newlinkref} ")

            # Repeating that logic for linkref.torellen 
            # First check if linkref.torellen is an exact match for the startposisjon / sluttposisjon columns
            if len( tempDF[ tempDF['startposisjon'] == linkref['torellen'] ] == 1 ):
                newlinkref['torellen'] = tempDF[ tempDF['startposisjon'] == linkref['torellen'] ].iloc[0]['super_startposisjon']
            elif len( tempDF[ tempDF['sluttposisjon'] == linkref['torellen'] ] == 1 ):
                newlinkref['torellen'] = tempDF[ tempDF['sluttposisjon'] == linkref['torellen'] ].iloc[0]['super_sluttposisjon']
            else: 
                # Doesn't match start/end points exactly, we must interpolate
                temp2DF = tempDF[ (tempDF['startposisjon'] <= linkref['torellen']) & (linkref['torellen'] <=  tempDF['sluttposisjon'] ) ]
                if len( temp2DF ) != 1: 
                    print( f"WARNING - there should exactly one row matching position {linkref['torellen']} @ link sequence {linkref['reflinkoid']}, found {len(temp2DF)} ")
                newlinkref['torellen'] = round( np.interp( linkref['torellen'], 
                                                        [ temp2DF.iloc[0]['startposisjon'], temp2DF.iloc[0]['sluttposisjon'] ], 
                                                        [ temp2DF.iloc[0]['super_startposisjon'], temp2DF.iloc[0]['super_sluttposisjon'] ] ), 8)    
                print( f"Interpolating torellen-position {linkref['torellen']} @ {linkref['reflinkoid']} => {newlinkref} ")                        

            mapped_NVDBroadlinklist.append( newlinkref )
            junk.append( newlinkref )

    #############################################
    # FINALLY - we have a mapping to the vegtrasé topology level, and can start to query NVDB api for data
    veglenkeposisjoner = [ str( x['fromrellen'] ) + '-' + str( x['torellen'] ) + '@' + str( int( x['reflinkoid'] ) ) for x in    mapped_NVDBroadlinklist ]
    
    # Take some precaution, if this list veglenkeposisjoner is long you need to iterate over (suitable large chunks of) this list.
    # There is an upper limit for how much text you can fit into HTTP GET query, ergo there is a limit for how many elements you can cram into 'veglenkesekvens' - parameter   
    # So we'll work with chunks of the list "veglenkeposisjoner"
    chunk_size = 25
    chunk_pointers = list( range( 0, len( veglenkeposisjoner ), chunk_size ))
    fartsgrense = [] # List to hold list of dictionaries from nvdbFagdata.to_records()

    # Working with pointers defining chunks of our list veglenkeposisjoner
    for pointerB, junk in enumerate( chunk_pointers ): 
        if pointerB == len( chunk_pointers)-1: # Last item, we need to go from that pointer to the end of the list
            fartsgrense.extend( nvdbapiv3.nvdbFagdata( 105, filter={'veglenkesekvens' : ','.join( veglenkeposisjoner[ chunk_pointers[pointerB]:] )} ).to_records() )
            print( f"Debug: fetching fartsgrense for veglenkesekvens list item {chunk_pointers[pointerB]} - last item in list ({len(veglenkeposisjoner)} items total)  ")
        else: 
            fartsgrense.extend( nvdbapiv3.nvdbFagdata( 105, filter={'veglenkesekvens' : ','.join( veglenkeposisjoner[ chunk_pointers[pointerB]:chunk_pointers[pointerB+1] ] ) } ).to_records() )
            print( f"Debug: fetching fartsgrense for veglenkesekvens list item {chunk_pointers[pointerB]} - {chunk_pointers[pointerB+1]}   ")

    fartsgrense = pd.DataFrame(  fartsgrense )   
    # Most likely, our chunk method will given us duplicates: Quering for  '0-0.4@625517' in one chunk and then '0.4-1@625517' might very well return the same object => duplicates
    print( f"Debug: Length of fartsgrense-data before duplicate removal: {len( fartsgrense)}")
    fartsgrense.drop_duplicates( subset=['nvdbId', 'versjon', 'veglenkesekvensid', 'startposisjon'], inplace=True  )
    print( f"Debug: Length of fartsgrense-data AFTER duplicate removal: {len( fartsgrense)}")

    fartsgrense['geometry'] = fartsgrense['geometri'].apply( wkt.loads )
    fartsgrense = gpd.GeoDataFrame( fartsgrense, geometry='geometry', crs=5973 )
    fartsgrense.to_file( 'demoruteplan.gpkg', layer='fartsgrense', driver='GPKG')

    routingdata = gpd.GeoDataFrame( routingdata, geometry='geometry', crs=5973)
    # cant save lists into a geopackage, so deleting the column with list of NVDB references
    routingdata.drop( columns='nvdbreferences', inplace=True )
    routingdata.to_file( 'demoruteplan.gpkg', layer='ruteforslag', driver='GPKG')