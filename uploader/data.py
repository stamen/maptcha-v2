from uuid import uuid1
from urllib import urlopen
from csv import DictReader

def create_atlas(domain, queue, url):
    '''
    '''
    row = DictReader(urlopen(url)).next()
    
    if 'address' not in row:
        raise ValueError('Missing "address" in %(url)s' % locals())
    
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
    
    return atlas.name
