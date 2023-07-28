import ruteplan 

from shapely import wkt 


if __name__ == '__main__': 

    p1 =  wkt.loads( 'POINT(262819.18 6649657.89 )' ) # Storgata 51, Oslo 
    p2 =  wkt.loads( 'POINT(260805.98 6649240.36 )' ) # Munkedamsveien 59, Oslo

    response =  ruteplan.anropruteplan( coordinates = [(p1.x, p1.y), (p2.x, p2.y) ]  )
    data = response.json()