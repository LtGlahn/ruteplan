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

import STARTHER
import ruteplan
from copy import deepcopy 

from shapely.geometry import shape

def ruteplan2dict( **kwargs ): 
    """
    Anrop ruteplantjenesten og få liste med dictionaries tilbake 

    NB! geometrien - feltet 'geometry' - er konvertert til shapely-objekter 

    Tynn wrapper rundt funksjonene anropruteplan (returnerer requests responsobjekt) 
    og parseruteplan (returnerer liste med geojson-features). Se dokumentasjonen for disse funksjonene 
    """

    data = None 
    r = anropruteplan( **kwargs )
    if r.ok: 
        features = parseruteplan( r )
        data = [] 
        for feat in features: 
            props = deepcopy( feat['properties'] )
            props['geometry'] = shape( feat['geometry'] )
            data.append( props )

    else: 
        print( f"Feilkode fra ruteplantjenesten {r.http_status} {r.text} ")

    return data 



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
    

def parseruteplan( responseobj, egenskaper={}, startvertices=None  ): 
    """Tar responsobjekt fra ruteplantjenesten, omsetter til en 
    liste med Geojson-features. Disse kan puttes inn i en featureCollection
    eller bearbeides med annet vis. 
    
    Hvis du har andre (meta)data som du vil knytte til ruteforslaget
    kan dette sendes inn som en dict til parameteren egenskaper={'key':'val'} 
    
    Parameteren startvertices=N (heltall) gir starten av ruta (maks N 
    koordinatpunkt regnet fra start). Nytting for kontroll av at startpunkt
    er der du vil ha det
    """
    
    # Feilsituasjoner? 
    if not responseobj.ok: 
        message= ' '.join( [ 'Invalid response from ruteplan:', 
                            str(r.status_code), r.reason, r.url ])
        raise ValueError( message )

    data = responseobj.json()
    if 'messages' in data.keys():
        message = str( data['messages']) + ' ' + responseobj.url
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
        egen2.update(attributes)
        
            
        # Parser listen med ekstra attributter
        if extra_attributes: 
            for val in extra_attributes:
                egen2[val['key']] = val['value']
            
        # Henter litt snacks fra directions-elementet:
        egen2['routeName'] = data['directions'][ii]['routeName']
        
        # Legger paa info om beste - nestbeste osv
        egen2['rutealternativNr'] = ii

        # NVDB veglenkesekvenser 
        if 'nvdbreferences' in rute: 
            egen2['nvdbreferences'] = rute['nvdbreferences']
        
        # Behandler geometri
        if startvertices: 
            mygeom =  geojson.LineString( rute['geometry']['paths'][0][:startvertices])
        else: 
            mygeom =  geojson.LineString( rute['geometry']['paths'][0])
        
        # Lager geojson-objekt
        mygeojs = geojson.Feature( geometry=mygeom, properties=egen2)


        featurelist.append( mygeojs)
          
    return featurelist

def anropruteplan( ruteplanparams={ 'format' :  'json', 'geometryformat' : 'isoz', 'returnNvdbReferences' : True }, 
                  server='ruteplan', coordinates = [ (269756.5,7038421.3), (269682.4,7039315.6)]): 
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
    
    # Siden vi modifiserer ruteplan-params så må vi kopiere, ellers kan du få kluss
    params = copy.deepcopy( ruteplanparams )

    # Har vi eksplisitt angitt "stops" i ruteplanparametrene? 
    # Hvis ikke bygger vi det ut fra koordinatene
    if not 'stops' in ruteplanparams.keys(): 
        cords = copy.deepcopy( coordinates)

        if len(cords) < 2: 
            raise ValueError( 'Coordinate list must have at least 2 points')
        
        stopstrings  = []
        while len(cords): 
            stopstrings.append( ','.join( str(px) for px in cords.pop(0))  )
        
        params['stops'] = ';'.join( stopstrings)
        
    if credentials['auth']:
        r = requests.get( credentials['url'], auth=credentials['auth'], 
                         params=params, proxies=proxies)
        
    else: 
        r = requests.get( credentials['url'], params=params, 
                         proxies=proxies)

    return r

def fiksvegdata2ruteplanparams( fiksvegdataparams ): 
    """
    Oversetter datastruktur fra fiksvegdata (sykkelveg.no feilmelding) til ruteplan parametre

    Eksempel på datastruktur fra fiksvegdata: 

    ```json
    {
        "routeType": 0,
        "effort": 0,
        "locations": [
            {
            "easting": 236501.43,
            "northing": 7073079.82,
            "elevation": 0
            },
            {
            "easting": 371248.035,
            "northing": 7265105.225,
            "elevation": 0
            }
        ],
        "barriers": "GEOMETRYCOLLECTION(POLYGON((269512.75097657 7042004.4277345, 
                                269438.70410157 7041660.638672,269920.00878907 7041242.8027345,
                                270295.53222657 7041501.966797,269512.75097657 7042004.4277345)),
                                POINT(264082.86718751 7017882.9970705))",
        "language": "no",
        "epsg": "EPSG:32633",
        "includeGML": false,
        "includeWKT": true,
        "avoidTrails": false
    }
    ```

    Som oversettes til 

    ```json
    { 
        "route_type" : "bike", 
        "stops" : "236501.43,7073079.82;371248.035,7265105.225" 
        "effort": 0, 
        "barriers" :  "GEOMETRYCOLLECTION(POLYGON((269512.75097657 7042004.4277345,
                                269438.70410157 7041660.638672,269920.00878907 7041242.8027345,
                                270295.53222657 7041501.966797,269512.75097657 7042004.4277345)),
                                POINT(264082.86718751 7017882.9970705))",
        "geometryformat" : "isoz", 
        "avoidTrails" : false

    }

    """

    false = False
    true = True

    assert 'locations' in fiksvegdataparams, "Må ha locations-data i fiksvegdata-parameter"
    assert isinstance( fiksvegdataparams['locations'], list), "Ugyldig datatype for locations-feltet (liste med dict)"
    assert isinstance( fiksvegdataparams['locations'][0], dict), "Ugyldig datatype for locations-feltet  (liste med dict)"
    assert 'easting' in fiksvegdataparams['locations'][0], "Location-element mangler data for 'easting'"
    assert 'northing' in fiksvegdataparams['locations'][0], "Location-element mangler data for 'northing'"
    assert len( fiksvegdataparams['locations'] ) > 1, "Location-element må ha minst to elementer"
    # Oversetter  [ { "easting" : x0, "northing" : y0 } ] => komma- og semikolonseparert tekststreng
    # "x0,y0;x1,y1;x2,y2" .... 
    stops =  ';'.join(  [ ','.join( [ str( x['easting']), str( x['northing']) ] ) 
                    for x in fiksvegdataparams['locations'] ] )

    ruteplanparams = {    "geometryformat"      : "isoz", 
                          "avoidTrails"         : False, 
                          "route_type"          : "bike",
                          "avoidTrails"         : False,
                        #   "barriers"            : "GEOMETRYCOLLECTION()", 
                          "format"              : "json",
                          "stops"               : stops 
    }

    # if 'barriers' in fiksvegdataparams:
    #     ruteplanparams['barriers'] = fiksvegdataparams['barriers']

    if 'effort' in fiksvegdataparams:
        ruteplanparams['effort'] = fiksvegdataparams['effort']

    if 'avoidTrails' in fiksvegdataparams:
        ruteplanparams['avoidTrails'] = fiksvegdataparams['avoidTrails']

    return ruteplanparams
