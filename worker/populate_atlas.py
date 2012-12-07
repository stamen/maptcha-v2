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
    
    err_msg = ""
    image = None
    try:
        body = StringIO(urlopen(map_url).read())
        image = Image.open(body)
    except IOError: 
        err_msg = "Could not open image."
    except:
        err_msg = "Problem with the image."
        
    if not image:
        map['status'] = 'error'
        map['aspect'] = '%.9f' % 1.0 
        map.save()
    else:
        #
        # Full-size image
        #
        key = bucket.new_key(map['image'])
        head = {'Content-Type': guess_type(map_url)[0]}
        key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')

        width, height = image.size[0], image.size[1]
        aspect = float(width) / float(height)

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
    
        map['status'] = 'uploaded'
        map['aspect'] = '%.9f' % aspect
        map.save()
    
    # update atlas status
    atlas = atlas_dom.get_item(map['atlas'],consistent_read=True) 
    q = "select count(*) from `%s` where atlas = '%s' and status = 'empty'"%(map_dom.name,map['atlas'])
    remaining = map_dom.select(q,consistent_read=True).next()
    if int(remaining['Count']) == 0:
        atlas['status'] = "uploaded"
        atlas.save()
    
    
    


