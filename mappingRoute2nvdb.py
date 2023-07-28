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

    # # Testcase for the switch of start- and sluttposisjon data values
    # # where startposisjon (fromrel) > sluttposisjon (torel) 
    # p1 = wkt.loads( 'POINT(262796.12164045224 6647150.737110766 )' )
    # p2 = wkt.loads( 'POINT(262449.76561430475 6649115.558134907 )' )

    ## Testcase for complaints about missing data - which turned out to be 
    ##  that the kjørebane link sequence  1878200 maps to TWO DIFFERENT 
    ## vegtrasé links sequences. So a much more complicated mapping mechanism...  
    # p1 = wkt.loads( 'POINT(262796.12164045224 6647150.737110766 )' )
    # p2 = wkt.loads( 'POINT(262449.76561430475 6649115.558134907 )' )

    # Saving the JSON response for documentation 
    response =  ruteplan.anropruteplan( coordinates = [(p1.x, p1.y), (p2.x, p2.y) ]  )
    data = response.json()
    with open( 'ruteplanrespons.json', 'w') as f: 
        json.dump( data, f, indent=4, ensure_ascii=False )

    # Making dataframe for the routing segments 
    routingdata = pd.DataFrame( ruteplan.ruteplan2dict( coordinates= [(p1.x, p1.y), (p2.x, p2.y) ] ))

    # List of NVDB linear positions @ link sequence from ruteplan data, one per "route" element 
    # one to three route alternatives may be provided.
    temp = []
    for route in data['routes']: 
        temp.extend( route['nvdbReferenceLinks'] )    

    # Rounding to 8 decimals precision for the linear positions 
    ruteplan_nvdblinks = []
    for linkref in temp: 
        linkref['fromLength'] = round( linkref['fromLength'], 8)
        linkref['toLength'] = round( linkref['toLength'], 8)
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
    for veglenkesekvensID in ruteplan_nvdblinksDF['nvdbReferenceId'].unique(): 
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

                # Ignoring historical (inactive) road links, i.e. those where "sluttdato" is set
                if not 'sluttdato' in lenke: 
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

        if linkref['nvdbReferenceId'] not in kjbn_topology:
            # No mapping nescessary, this link sequence is at the VT topology level 
            mapped_NVDBroadlinklist.append( linkref )

        else: 
            # Maping from kjørebane => vegtrasé using superstedfesting
            tempDF0 = NVDBroadlinkDF[ NVDBroadlinkDF['veglenkesekvensid'] == linkref['nvdbReferenceId']]
            # There can be mapping to MULTIPLE vegtrasé from a single kjørebane link sequence
            # Example: https://nvdbapiles-v3.atlas.vegvesen.no/vegnett/veglenkesekvenser/1878200.json
            # which maps to TWO vegtrasé in the superstedfesting: 1878165 and 1878201 
            # So we must iterate over each superstedfesting-veglenkeksekvens in tempDF

            for minSuperVeglenkesekvens in tempDF0['super_veglenkesekvensid'].unique(): 

                tempDF = tempDF0[ tempDF0['super_veglenkesekvensid'] == minSuperVeglenkesekvens ]
                newlinkref = { 'kjbane' : linkref, 'nvdbReferenceId' : int( minSuperVeglenkesekvens )  }

                # First check if linkref.fromLength is an exact match for the startposisjon / sluttposisjon columns
                # OR if the start/sluttposisjon has a larger extent than our roadlinks
                # This can happen when our kjørebane maps to multiple vegtrasé links
                if len( tempDF[ tempDF['startposisjon'] == linkref['fromLength'] ] == 1 ):
                    newlinkref['fromLength'] = tempDF[ tempDF['startposisjon'] == linkref['fromLength'] ].iloc[0]['super_startposisjon']
                elif len( tempDF[ tempDF['sluttposisjon'] == linkref['fromLength'] ] == 1 ):
                    newlinkref['fromLength'] = tempDF[ tempDF['sluttposisjon'] == linkref['fromLength'] ].iloc[0]['super_sluttposisjon']
                elif linkref['fromLength'] < tempDF['startposisjon'].min(): 
                    newlinkref['fromLength'] = tempDF['startposisjon'].min()

                else: 
                    # Doesn't match start/end points exactly, we must interpolate
                    temp2DF = tempDF[ (tempDF['startposisjon'] <= linkref['fromLength']) & (linkref['fromLength'] <=  tempDF['sluttposisjon'] ) ]
                    if len( temp2DF ) != 1: 
                        print( f"WARNING - there should exactly one row matching position {linkref['fromLength']} @ link sequence {linkref['nvdbReferenceId']}, found {len(temp2DF)} ")
                    newlinkref['fromLength'] = round( np.interp( linkref['fromLength'], 
                                                                [ temp2DF.iloc[0]['startposisjon'], temp2DF.iloc[0]['sluttposisjon'] ], 
                                                                [ temp2DF.iloc[0]['super_startposisjon'], temp2DF.iloc[0]['super_sluttposisjon'] ]  ), 8)                
                    print( f"Interpolating fromLength-position {linkref['fromLength']} @ {linkref['nvdbReferenceId']} => {newlinkref} ")

                # Repeating that logic for linkref.toLength 
                # First check if linkref.toLength is an exact match for the startposisjon / sluttposisjon columns
                if len( tempDF[ tempDF['startposisjon'] == linkref['toLength'] ] == 1 ):
                    newlinkref['toLength'] = tempDF[ tempDF['startposisjon'] == linkref['toLength'] ].iloc[0]['super_startposisjon']
                elif len( tempDF[ tempDF['sluttposisjon'] == linkref['toLength'] ] == 1 ):
                    newlinkref['toLength'] = tempDF[ tempDF['sluttposisjon'] == linkref['toLength'] ].iloc[0]['super_sluttposisjon']
                elif linkref['toLength'] > tempDF['sluttposisjon'].max(): 
                    newlinkref['toLength'] = tempDF['sluttposisjon'].max()
                else: 
                    # Doesn't match start/end points exactly, we must interpolate
                    temp2DF = tempDF[ (tempDF['startposisjon'] <= linkref['toLength']) & (linkref['toLength'] <=  tempDF['sluttposisjon'] ) ]
                    if len( temp2DF ) != 1: 
                        print( f"WARNING - there should exactly one row matching position {linkref['toLength']} @ link sequence {linkref['nvdbReferenceId']}, found {len(temp2DF)} ")
                    newlinkref['toLength'] = round( np.interp( linkref['toLength'], 
                                                            [ temp2DF.iloc[0]['startposisjon'], temp2DF.iloc[0]['sluttposisjon'] ], 
                                                            [ temp2DF.iloc[0]['super_startposisjon'], temp2DF.iloc[0]['super_sluttposisjon'] ] ), 8)    
                    print( f"Interpolating toLength-position {linkref['toLength']} @ {linkref['nvdbReferenceId']} => {newlinkref} ")                        

                mapped_NVDBroadlinklist.append( newlinkref )
                junk.append( newlinkref )

    #############################################
    # FINALLY - we have a mapping to the vegtrasé topology level, and can start to query NVDB api for data

    # veglenkeposisjoner = [ str( x['fromLength'] ) + '-' + str( x['toLength'] ) + '@' + str( int( x['nvdbReferenceId'] ) ) for x in    mapped_NVDBroadlinklist ]
    veglenkeposisjoner = [ str( min(x['fromLength'], x['toLength']) ) + '-' + str( max(x['fromLength'], x['toLength']) ) + '@' + str( int( x['nvdbReferenceId'] ) ) for x in    mapped_NVDBroadlinklist ]

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
    routingdata.to_file( 'demoruteplan.gpkg', layer='ruteforslag', driver='GPKG')