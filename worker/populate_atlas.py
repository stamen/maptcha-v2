from uuid import uuid1
from csv import DictReader
from urllib import urlopen
from StringIO import StringIO
from os.path import basename, splitext
from urlparse import urljoin, urlparse
from mimetypes import guess_type
import re
from PIL import Image 

reserved_keys = ['image','large','thumb','atlas']
def normalize_key(key):
    key = slugify(key)
     
    if key in reserved_keys:
        key = "__" + key 
        
    return key
    
def slugify(w):
    w = w.strip().lower()
    return re.sub(r'\W+','_',w)
    
def populate_atlas(atlas_dom, map_dom, bucket, id):
    '''
    '''
    atlas = atlas_dom.get_item(id)
    
    if 'href' not in atlas:
        raise ValueError('Missing "href" in atlas %(id)s' % locals())
    
    
    #normalize keys
    normalized = []
    for (index, row) in enumerate(DictReader(urlopen(atlas['href']))):
        obj = {}
        for item in row:
            norm_key = normalize_key(item)
            obj[norm_key] = row[item]
        normalized.append(obj)
    
    for row in normalized:
        if row['image_url'].find('http') == 0:
            map_url = row['image_url']
        else:
            map_url = urljoin(atlas['href'], row['image_url'])
        
    
        map_name = slugify(row['map_title'])

        create_atlas_map(map_dom, bucket, atlas.name, map_url, map_name, row)
    
    atlas['status'] = 'uploaded'
    atlas.save()

def create_atlas_map(map_dom, bucket, atlas_id, map_url, map_name, row):
    '''
    '''
    scheme, host, path, q, p, f = urlparse(map_url)
    
    image_name = basename(path)
    
    map = map_dom.new_item(str(uuid1()))
    map['image'] = 'maps/%s/%s' % (map.name, image_name)
    map['large'] = 'maps/%s/%s-large.jpg' % (map.name, splitext(image_name)[0])
    map['thumb'] = 'maps/%s/%s-thumb.jpg' % (map.name, splitext(image_name)[0])
    map['atlas'] = atlas_id  
    
    for item in row:
        map[item] = row[item]
    
    #
    # Full-size image
    #
    key = bucket.new_key(map['image'])
    head = {'Content-Type': guess_type(map_url)[0]}
    body = StringIO(urlopen(map_url).read())

    key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')
    image = Image.open(body)
    
    #
    # Large image
    #
    key = bucket.new_key(map['large'])
    head = {'Content-Type': 'image/jpeg'}
    body = StringIO()

    image.thumbnail((2048, 2048), Image.ANTIALIAS)
    image.save(body, 'JPEG')
    key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')

    #
    # Thumbnail image
    #
    key = bucket.new_key(map['thumb'])
    head = {'Content-Type': 'image/jpeg'}
    body = StringIO()

    image.thumbnail((150, 150), Image.ANTIALIAS)
    image.save(body, 'JPEG')
    key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')

    map.save()
