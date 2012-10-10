from os import environ
from uuid import uuid1
from urllib import urlopen
from csv import DictReader
from os.path import basename
from urlparse import urljoin, urlparse
from mimetypes import guess_type

from util import connect_domain, connect_queue, connect_bucket

def populate_atlas(atlas_dom, map_dom, bucket, id):
    '''
    '''
    atlas = atlas_dom.get_item(id)
    
    if 'href' not in atlas:
        raise ValueError('Missing "href" in atlas %(id)s' % locals())
    
    for (index, row) in enumerate(DictReader(urlopen(atlas['href']))):
        
        map_url = urljoin(atlas['href'], row['address'])
        map_name = row.get('name', 'Untitled Map #%d' % (index + 1))
        
        scheme, host, path, q, p, f = urlparse(map_url)
        
        map = map_dom.new_item(str(uuid1()))
        map['image'] = 'maps/%s/%s' % (map.name, basename(path))
        map['atlas'] = atlas.name
        
        key = bucket.new_key(map['image'])
        head = {'Content-Type': guess_type(map_url)[0]}
        body = urlopen(map_url).read()

        key.set_contents_from_string(body, headers=head, policy='public-read')
        
        map.save()
    
    atlas['status'] = 'uploaded'
    atlas.save()

if __name__ == '__main__':

    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']

    bucket = connect_bucket(key, secret, prefix+'stuff')
    queue = connect_queue(key, secret, prefix+'jobs')
    
    try:
        message = queue.get_messages(visibility_timeout=5)[0]
        msg = message.get_body()

    except IndexError:
        pass

    else:
        if msg.startswith('populate atlas '):
            print msg
            
            map_dom = connect_domain(key, secret, prefix+'maps')
            atlas_dom = connect_domain(key, secret, prefix+'atlases')

            populate_atlas(atlas_dom, map_dom, bucket, msg[len('populate atlas '):])
        
        queue.delete_message(message)
