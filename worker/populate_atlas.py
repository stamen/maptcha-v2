from urllib import urlopen
from StringIO import StringIO
from os.path import basename, splitext
from urlparse import urljoin, urlparse
from mimetypes import guess_type
from PIL import Image 

def create_atlas_map(atlas_dom, map_dom, bucket, map_id):
    '''
    '''
    map = map_dom.get_item(map_id,consistent_read=True)
    map_url = map['image_url']
    #atlas = atlas_dom.get_item(map['atlas'],consistent_read=True)
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
    
    map['status'] = 'finished'
    map.save()


