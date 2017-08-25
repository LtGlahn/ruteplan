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
    

def anropruteplan( ruteplanparams={ 'format' :  'json', 'geometryformat' : 'isoz' }, 
                  server='ruteplan', coordinates = [(274327.47280083, 6656639.067924), 
                   (275727.78289313,6656983.0269452)]): 
    """Fetch data from the NVDB roting API 
    
    ruteplanparams = dict with parameters for the routing applications. 
    If this dict doesn't have a  "stops" element it will be populated from the 
    coordinate list. 

    coordinates = list of tuples with (x,y ) coordinates. Must have at least 
    2 members. 
    
    Server is an element in the credentials.json-file. 
    
    Returns a request response object
    """

	# Henter info om server, pålogging etc
    credentials = lescredfil( credfile='credentials.json', server=server)
        
    
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
                         params=ruteplanparams)
        
    else: 
        r = requests.get( credentials['url'], params=ruteplanparams)
        
    return r