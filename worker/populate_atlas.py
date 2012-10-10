from uuid import uuid1
from csv import DictReader
from urllib import urlopen
from StringIO import StringIO
from os.path import basename, splitext
from urlparse import urljoin, urlparse
from mimetypes import guess_type

from PIL import Image

def populate_atlas(atlas_dom, map_dom, bucket, id):
    '''
    '''
    atlas = atlas_dom.get_item(id)
    
    if 'href' not in atlas:
        raise ValueError('Missing "href" in atlas %(id)s' % locals())
    
    for (index, row) in enumerate(DictReader(urlopen(atlas['href']))):
        
        map_url = urljoin(atlas['href'], row['address'])
        map_name = row.get('name', 'Untitled Map #%d' % (index + 1))
        
        create_atlas_map(map_dom, bucket, atlas.name, map_url, map_name)
    
    atlas['status'] = 'uploaded'
    atlas.save()

def create_atlas_map(map_dom, bucket, atlas_id, map_url, map_name):
    '''
    '''
    scheme, host, path, q, p, f = urlparse(map_url)
    
    image_name = basename(path)
    
    map = map_dom.new_item(str(uuid1()))
    map['image'] = 'maps/%s/%s' % (map.name, image_name)
    map['large'] = 'maps/%s/%s-large.jpg' % (map.name, splitext(image_name)[0])
    map['thumb'] = 'maps/%s/%s-thumb.jpg' % (map.name, splitext(image_name)[0])
    map['atlas'] = atlas_id
    
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

    image.thumbnail((800, 800), Image.ANTIALIAS)
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
