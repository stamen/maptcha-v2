from urllib import urlopen
from StringIO import StringIO
from os.path import basename, splitext
from urlparse import urljoin, urlparse
from mimetypes import guess_type
from PIL import Image 
from urllib import unquote_plus, quote_plus

def create_atlas_map(mysql, bucket, map_id):
    '''
    '''
    mysql.execute('''SELECT * FROM maps WHERE id = %s''', (map_id, ))
    map = mysql.fetchdict()
    
    map_url = map['original']
    
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
        
        mysql.execute('UPDATE maps SET status=%s, aspect=%s WHERE id = %s',
                      (map['status'], map['aspect'], map['id']))
        
    else:
        # NOTE: decoding map image names, because S3 will double encode
        
        #
        # Full-size image
        #
        key = bucket.new_key(unquote_plus(map['image']))
        head = {'Content-Type': guess_type(map_url)[0]}
        key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')

        width, height = image.size[0], image.size[1]
        aspect = float(width) / float(height)

        #
        # Large image
        #
        key = bucket.new_key(unquote_plus(map['large']))
        head = {'Content-Type': 'image/jpeg'}
        body = StringIO()

        image.thumbnail((2048, 2048), Image.ANTIALIAS)
        image.save(body, 'JPEG')
        key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read')

        #
        # Thumbnail image
        #
        key = bucket.new_key(unquote_plus(map['thumb']))
        head = {'Content-Type': 'image/jpeg'}
        body = StringIO()

        image.thumbnail((150, 150), Image.ANTIALIAS)
        image.save(body, 'JPEG')
        key.set_contents_from_string(body.getvalue(), headers=head, policy='public-read') 
    
        map['status'] = 'uploaded'
        map['aspect'] = '%.9f' % aspect
        
        mysql.execute('UPDATE maps SET status=%s, aspect=%s WHERE id = %s',
                      (map['status'], map['aspect'], map['id']))
    
    mysql.execute('''SELECT COUNT(id) AS count FROM maps
                     WHERE atlas_id = %s AND status = 'empty' ''',
                  (map['atlas_id'], ))

    remaining = mysql.fetchdict()
    
    if remaining['count'] == 0:
        mysql.execute("UPDATE atlases SET status = 'uploaded' WHERE id = %s", (map['atlas_id'], ))
