from uuid import uuid1
from time import time

from util import connect_domain

from boto.exception import SDBResponseError

def generate_id():
    '''
    '''
    return str(uuid1())

def connect_domains(key, secret, prefix):
    '''
    '''
    suffixes = 'atlases', 'maps', 'rough_placements'
    domains = [connect_domain(key, secret, prefix+suffix) for suffix in suffixes]
    
    return domains

def place_roughly(map_dom, place_dom, map, ul_lat, ul_lon, lr_lat, lr_lon):
    '''
    '''
    #
    # Generate a new placement and save it.
    #
    placement = place_dom.new_item(generate_id())
    
    placement['map'] = map.name
    placement['timestamp'] = int(time())
    placement['ul_lat'] = '%.8f' % ul_lat
    placement['ul_lon'] = '%.8f' % ul_lon
    placement['lr_lat'] = '%.8f' % lr_lat
    placement['lr_lon'] = '%.8f' % lr_lon
    placement.save()
    
    #
    # Update the map item with current placement agreement.
    # Try a few times in case of race conditions.
    #
    for attempt in (1, 2, 3):
        try:
            update_map_rough_consensus(map_dom, place_dom, map)
            break
        except SDBResponseError, e:
            if attempt == 3:
                raise

def update_map_rough_consensus(map_dom, place_dom, map):
    '''
    '''
    #
    # Get all other existing placements and fresh version of the map.
    #
    q = 'select * from `%s` where map = "%s"' % (place_dom.name, map.name)
    placements = list(place_dom.select(q))
    map = map_dom.get_item(map.name)
    
    if len(placements):
        #### combine the placements to come up with consensus
        ul_lat = '%.8f' % (sum([float(p['ul_lat']) for p in placements]) / len(placements))
        ul_lon = '%.8f' % (sum([float(p['ul_lon']) for p in placements]) / len(placements))
        lr_lat = '%.8f' % (sum([float(p['lr_lat']) for p in placements]) / len(placements))
        lr_lon = '%.8f' % (sum([float(p['lr_lon']) for p in placements]) / len(placements))
    
    consensus = dict(ul_lat=ul_lat, ul_lon=ul_lon, lr_lat=lr_lat, lr_lon=lr_lon)
    
    #
    # Update the map with new information
    #
    
    if 'version' not in map:
        consensus['version'] = 1
        map_dom.put_attributes(map.name, consensus, expected_value=['version', False])
    
    else:
        consensus['version'] = 1 + int(map['version'])
        map_dom.put_attributes(map.name, consensus, expected_value=['version', map['version']])
