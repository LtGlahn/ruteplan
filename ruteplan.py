# -*- coding: utf-8 -*-

"""Python-functions for routing directions from the Norwegian Public Road Administration 
routing API https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil

You must have the file credentials.json in your working directory with this 
content: 
    
{
	"ruteplan": {
		"pw": "yourpassword",
		"user": "yourUserName",
		"url": "https://www.vegvesen.no/ruteplan/routingservice_v1_0/routingservice/solve"
	}
}



"""

import requests
import json
import copy
import geojson

def lescredfil( credfile = 'credentials.json', server='ruteplan' ):
  
    try: 
    	with open( credfile) as f:
    		cred = json.load( f)
		
    except FileNotFoundError: 
        print( 'You must have the file ', credfile, 'in your working dir')
        print( 'Use credentials-template.json as template for creating it')
        raise
        
    try: 
        credentials = cred[server]
        junk = credentials['url']
    except KeyError: 
        print( 'Missing data in ', credfile)
        print( 'Have a look at credentials-template.json for inspiration' )
        raise
        
    # Sjekker om det er oppgitt brukernavn og passord
    test = set(['pw', 'user'])
    if test.issubset( set(credentials)) and credentials['pw'] and \
                                                        credentials['user']:
        credentials['auth'] = ( credentials['user'], credentials['pw'])
    else: 
        credentials['auth'] = None
        
    return credentials
    

def parseruteplan( responseobj, egenskaper={}  ): 
    """Tar responsobjekt fra ruteplantjenesten, omsetter til en 
    liste med Geojson-features. Disse kan puttes inn i en featureCollection
    eller bearbeides med annet vis. 
    
    Hvis du har andre (meta)data som du vil knytte til ruteforslaget
    kan dette tas med via parameteren egenskaper={'key':'val'} 
    """
    
    # Feilsituasjoner? 
    if not responseobj.ok: 
        message= ' '.join( [ 'Invalid response from ruteplan:', 
                            str(r.status_code), r.reason, r.url ])
        raise ValueError( message )

    data = responseobj.json()
    if 'messages' in data.keys():
        message = str( data['messages']) + ' ' + r.url
        raise ValueError( message)

    featurelist = []
    for ii, rute in enumerate( data['routes']['features']): 
        
        # Fjerner de egenskapene vi ikke vil ha: 
        attributes = rute['attributes']
        extra_attributes = attributes.pop( 'attributes')
        attributes.pop( 'ObjectID')
        attributes.pop('Shape_Length')
        
        # Lager attributtliste av de egenskapene som er igjen: 
        egen2 = copy.deepcopy( egenskaper)
        for k in attributes.keys():
            egen2[k] = attributes[k]
            
        # Parser listen med ekstra attributter
        for val in extra_attributes:
            egen2[val['key']] = val['value']
            
        # Henter litt snacks fra directions-elementet: 
        egen2['routeName'] = data['directions'][ii]['routeName']
        
        # Legger på info om beste - nestbeste osv
        egen2['rutealternativNr'] = ii
        
        # Behandler geometri
        mygeom =  geojson.LineString( rute['geometry']['paths'][0])
        
        # Lager geojson-objekt
        mygeojs = geojson.Feature( geometry=mygeom, properties=egen2)


        featurelist.append( mygeojs)
          
    return featurelist

def anropruteplan( ruteplanparams={ 'format' :  'json', 'geometryformat' : 'isoz' }, 
                  server='ruteplan', coordinates = 
    [ (269756.5,7038421.3), (269682.4,7039315.6)]): 
    """Fetch data from the NVDB roting API 
    
    ruteplanparams = dict with parameters for the routing applications. 
    If this dict doesn't have a  "stops" element it will be populated from the 
    coordinate list. 

    coordinates = list of tuples with (x,y ) coordinates. Must have at least 
    2 members. 
    
    Server is an element in the credentials.json-file. 
    
    Returns a request response object
    """

	# Henter info om server, brukernavn etc
    credentials = lescredfil( credfile='credentials.json', server=server)
    
    # Har vi angitt proxy? 
    proxies = {}
    if 'proxies' in credentials.keys(): 
        proxies = credentials['proxies']
    
    # Har vi eksplisitt angitt "stops" i ruteplanparametrene? 
    # Hvis ikke bygger vi det ut fra koordinatene
    if not 'stops' in ruteplanparams.keys(): 
        cords = copy.deepcopy( coordinates)
        
        if len(cords) < 2: 
            raise ValueError( 'Coordinate list must have at least 2 points')
        
        stopstrings  = []
        while len(cords): 
            stopstrings.append( ','.join( str(px) for px in cords.pop(0))  )
        
        ruteplanparams['stops'] = ';'.join( stopstrings)
        
    if credentials['auth']:
        r = requests.get( credentials['url'], auth=credentials['auth'], 
                         params=ruteplanparams, proxies=proxies)
        
    else: 
        r = requests.get( credentials['url'], params=ruteplanparams, 
                         proxies=proxies)
        
    return r

