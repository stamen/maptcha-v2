from uuid import uuid1
from time import time
from random import choice
from urllib import urlopen 
from os.path import basename, splitext 
from urlparse import urljoin, urlparse
from csv import DictReader
import re 

from util import connect_domain, check_url

from boto.exception import SDBResponseError

required_fields = ['map_title', 'date', 'image_url']
reserved_keys = ['image','large','thumb','atlas','version'] #map

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
    errors = []
    for field in required_fields: 
        if field not in keys:
            errors.append(field)
        
    return errors

def slugify(w):
    w = w.strip().lower()
    return re.sub(r'\W+','_',w)
        
def normalize_rows(rows):
    normalized = []
    for row in rows:
        obj = {}
        for item in row:
            norm_key = slugify(item)

            if norm_key in reserved_keys:
                norm_key = "__" + norm_key
                
            obj[norm_key] = row[item]
        normalized.append(obj) 
        
    return normalized
    
def create_atlas(domain, map_dom, queue, url, name, affiliation):
    '''
    ''' 
    temp = None 
    if not check_url(url):
        return {'error':"There's no file at that URL: <a href='%s'>%s</a>. Please <a href='/upload'>try again</a>."%(url,url)} 
    
    try:
        temp = DictReader(urlopen(url))
    except IOError:
        return {'error':"There's no file at that URL: <a href='%s'>%s</a>. Please <a href='/upload'>try again</a>."%(url,url)}
    
    if not temp.fieldnames:
        return {'error':"We couldn't work out if that file is even a CSV. Can you grab the URL again, and try another <a href='/upload'>upload</a>?"}
    
    try:
        rows = normalize_rows(list(temp))
    except:
        return {'error':"We couldn't work out if that file is even a CSV. Can you grab the URL again, and try another <a href='/upload'>upload</a>?"}  
        
    
    
    
    # normalize keys
    #keys = [key.lower().replace(' ', '_') for key in rows[0].keys()]
    
    missing_fields = validate_required_fields(rows[0].keys()) 
    
    #
    # validate fields
    #
    if len(missing_fields) > 0:
        return {'error':"Your CSV doesn't have all the required columns. You must include map_title, date and image_url.<br/>Please <a href='/upload'>try again</a>."}
    
    #
    # validate images
    # 
    
    # need to know the image_col name
    #img_col = filter(lambda x: x.lower().replace(' ', '_') == "image_url", rows[0].keys())[0]
    invalids = []
    for idx, row in enumerate(rows):
        row_num = idx+1
        for req in required_fields:
            if not row[req]:
                invalids.append({'idx':row_num,'err':"Missing %s"%req})
        
        if row['image_url']:    
            valid_url = check_url(row['image_url'])
            if not valid_url:
                invalids.append({'idx':row_num,'err':"Couldn't find an image at <a href='%s'>%s</a>"%(row['image_url'],row['image_url'])})
            
    if len(invalids):
        return {'error':"Some of your map entries don't work, because...","rows":invalids} 
    

    #if 'address' not in row:
        #raise ValueError('Missing "address" in %(url)s' % locals())

    #
    # Add an entry for the atlas to the atlases table.
    #
    atlas = domain.new_item(str(uuid1()))
    atlas['href'] = url
    atlas['timestamp'] = time()
    atlas['title'] = name
    atlas['affiliation'] = affiliation
    atlas['map_count'] = len(rows)
    atlas['status'] = 'processing maps'
    atlas.save()
    
    #
    # add maps
    #
    for row in rows:
        scheme, host, path, q, p, f = urlparse(row['image_url'])

        image_name = basename(path)
        map = map_dom.new_item(str(uuid1()))
        map['image'] = 'maps/%s/%s' % (map.name, image_name)
        map['large'] = 'maps/%s/%s-large.jpg' % (map.name, splitext(image_name)[0])
        map['thumb'] = 'maps/%s/%s-thumb.jpg' % (map.name, splitext(image_name)[0])
        map['atlas'] = atlas.name
        map['status'] = 'empty'
        
        for item in row:
            map[item] = row[item]
            
        map.save() 
        
        message = queue.new_message('create map %s' % map.name)
        queue.write(message)


    return {'success':atlas}

             
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
