from os import environ
from uuid import uuid1
from urllib import urlopen
from csv import DictReader
from os.path import basename
from urlparse import urljoin, urlparse
from mimetypes import guess_type

from boto import connect_s3, connect_sdb, connect_sqs
from boto.exception import SDBResponseError

def connect_domain(key, secret, name):
    ''' Return a connection to a simpledb domain for atlases.
    '''
    sdb = connect_sdb(key, secret)
    
    try:
        domain = sdb.get_domain(name)
    except SDBResponseError:
        domain = sdb.create_domain(name)
    
    return domain

def connect_queue(key, secret, name):
    '''
    '''
    sqs = connect_sqs(key, secret)
    queue = sqs.get_queue(name)
    
    return queue

def connect_bucket(key, secret, name):
    '''
    '''
    s3 = connect_s3(key, secret)
    bucket = s3.get_bucket(name)
    
    return bucket

def create_atlas(atlas_dom, map_dom, bucket, id):
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
        if msg.startswith('create atlas '):
            print msg
            
            map_dom = connect_domain(key, secret, prefix+'maps')
            atlas_dom = connect_domain(key, secret, prefix+'atlases')

            create_atlas(atlas_dom, map_dom, bucket, msg[len('create atlas '):])
        
        queue.delete_message(message)
