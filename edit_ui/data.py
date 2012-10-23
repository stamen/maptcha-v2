from uuid import uuid1
from time import time
from random import choice
from urllib import urlopen
from csv import DictReader

from util import connect_domain

from boto.exception import SDBResponseError

required_fields = ['map_title', 'date', 'image_url']

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
    
def validate_required_fields(keys):
    errors = 0
    for field in required_fields: 
        if field not in keys:
            errors += 1
        
    return errors
    
def create_atlas(domain, queue, url):
    '''
    '''
    row = DictReader(urlopen(url)).next()
    
    # normalize keys
    keys = [key.lower().replace(' ', '_') for key in row.keys()]
    
    missing_fields = validate_required_fields(keys) 
    
    #
    if missing_fields > 0:
        return {'error':"missing keys"}
        
    #if 'address' not in row:
        #raise ValueError('Missing "address" in %(url)s' % locals())

    #
    # Add an entry for the atlas to the atlases table.
    #
    atlas = domain.new_item(str(uuid1()))
    atlas['href'] = url
    atlas['status'] = 'empty'
    atlas.save()

    #
    # Queue the atlas for processing.
    #
    message = queue.new_message('populate atlas %s' % atlas.name)
    queue.write(message)

    return {'success':atlas.name}
                   
def choose_map(map_dom, atlas_id=None, skip_map_id=None):
    '''
    '''
    q = ['select * from `%s`' % (map_dom.name), 'limit 100']
    
    if atlas_id:
        q.insert(1, 'where atlas = "%s"' % atlas_id)
    
    maps = list(map_dom.select(' '.join(q)))
    map = choice(maps)
    
    while map.name == skip_map_id and len(maps) > 1:
        map = choice(maps)
        
    return map

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
    placements = list(place_dom.select(q, consistent_read=True))
    map = map_dom.get_item(map.name, consistent_read=True)
    
    if len(placements) == 0:
        raise Exception("Got no placements - why?")
    
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
