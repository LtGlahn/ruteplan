# -*- coding: utf-8 -*-

"""Python-functions for routing directions from the Norwegian Public Road Administration 
routing API https://data.norge.no/data/statens-vegvesen/api-ruteplantjeneste-bil

You must have the file credentials.json in your working directory with this 
content: 
    
{
    "ruteplan": {
        "pw": "yourpassword",
        "user": "yourUserName",
        "url": "https://www.vegvesen.no/ws/no/vegvesen/ruteplan/routingservice_v3_0/routingService/api/Route/best"
    }
}



"""

import requests
import json
import copy
from requests.auth import HTTPBasicAuth

import geojson

# import STARTHER
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
        print( f"Feilkode fra ruteplantjenesten HTTP STATUS={r.status_code} {r.text} ")
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
    if 'user' in credentials and 'pw' in credentials:
        user = credentials.pop( 'user')
        pw   = credentials.pop( 'pw')
        credentials['auth'] = HTTPBasicAuth( user, pw )
    else: 
        credentials['auth'] = None
        
    return credentials
    

def parseruteplan( responseobj, egenskaper={} ): 
    """Tar responsobjekt fra ruteplantjenesten, omsetter til en 
    liste med Geojson-features. Disse kan puttes inn i en featureCollection
    eller bearbeides med annet vis. 
    
    I ruteplan V3 er geojson brukt som datastruktur for hvert ruteforslag (inntil tre ruteforslag).
    Hvert ruteforslag har en del overordnet statistikk (lengde, kjøretid, kostnad bompenger etc), 
    samt hver geometribit som geojson-features. Denne funksjonen føyer informasjon fra rot-nivå til 
    "properties" - elementet på hver enkel geojson-element. 

    Hvis du har andre (meta)data som du vil knytte til ruteforslaget
    kan dette sendes inn som en dict til parameteren egenskaper={'key':'val'} 

    ARGUMENTS
        response : http requests response object https://requests.readthedocs.io/en/latest/

    KEYWORDS
        egenskaper : dictionary, ekstra metadata / data som føyes til hvert enkelt geojson-element

    RETURNS
        features : list of dictionaries, liste med gejoson features. 

    """
    
    # Feilsituasjoner? 
    if not responseobj.ok: 
        message= ' '.join( [ 'Invalid response from ruteplan:', 
                            str(responseobj.status_code), responseobj.reason, responseobj.url ])
        raise ValueError( message )

    data = responseobj.json()
    if 'messages' in data.keys():
        message = str( data['messages']) + ' ' + responseobj.url
        raise ValueError( message)

    featurelist = []
    for ii, rute in enumerate( data['routes'] ): 
        
        metadata = deepcopy( rute ) 
        metadata.pop('features', None )
        metadata.pop('nvdbReferenceLinks', None )
        metadata['rutealternativNr'] = ii
        if egenskaper: 
            metadata.update( egenskaper )
        
        for feature in rute['features']: 
            feature['properties'].update( metadata )
            featurelist.append(  feature ) 
          
    return featurelist

def anropruteplan( ruteplanparams={ 'ReturnFields' : ['Geometry', 'NvdbReferences'] }, 
                  server='ruteplan', coordinates = [ (269756.5,7038421.3), (269682.4,7039315.6)], debug=False, **kwargs ): 
    """Fetch data from the NVDB roting API 

    Please note that there are two ways  to specify the ruteplan parameters: 
      * One method is to specify all (or a subset of) ruteplan API parameters as elements of these two keywords 
            => 'ruteplanparams' keyword dict 
                Each tag - value of the 'ruteplanparams' dictionary is passed directly to the ruteplan API

            => 'coordinates' keyword, which is a list of 2D tuples

      * The other method is to pass parameters as named keywords - example 
            > anropruteplan( stops='277648.7,6760327.3;292465.4,6695768.8')
        Any keyword will override the values of the "ruteplanparams" and "coordinates" keywords. 

    Please consult the ruteplan API documentation for details https://labs.vegdata.no/ruteplandoc/
    
    ARGUMENTS: 
        None 

    KEYWORDS: 
        ruteplanparams = dict with parameters for the routing applications. 
        If this dict doesn't have a  "stops" element it will be populated from the 
        coordinate list. 

        coordinates = list of tuples with (x,y ) coordinates. Must have at least 
        2 members. 
        
        Server = 'ruteplan' is an element in the credentials.json-file. 

        debug = False If true, prints debug information. 

        Any other keyword is passed directly to the ruteplan API. These additional 
        keywords will override the values of the "ruteplanparams" or "coordinates" keywords
        https://labs.vegdata.no/ruteplandoc/
    
    RETURNS: 
        Returns a request response object https://requests.readthedocs.io/en/latest/ 
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


    # Any other keywords? These will override the values of the "ruteplanparams" or "coordinates" keywords
    for key, value in kwargs.items(): 
        params[key] = value

    if credentials['auth']:
        r = requests.get( credentials['url'], auth=credentials['auth'], 
                         params=params, proxies=proxies)
        
    else: 
        r = requests.get( credentials['url'], params=params, 
                         proxies=proxies)

    if debug:
        print( f"Ruteplan parametre: {json.dumps(params, indent=4)}")

    return r

