from uuid import uuid1
from urllib import urlopen
from csv import DictReader
required_fields = ['map_title','date','image_url']  

def normalize_key(key):
    return key.replace(" ","_").lower()
    
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
    
    #validate keys
    keys = []
    for key in row:
        keys.append( normalize_key(key) ) 
    
    fields_ok = validate_required_fields(keys) 
    
    #
    if fields_ok > 0:
        return {'error':"missing keys"}
        
    else:
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
                   