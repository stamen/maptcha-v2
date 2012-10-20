from os import environ
import logging    

from os.path import realpath, dirname, join, exists 

from util import connect_domain, connect_queue, connect_bucket, get_config_vars
from populate_atlas import populate_atlas

key, secret, prefix = get_config_vars(dirname(__file__)) 
#key, secret, prefix = environ['key'], environ['secret'], environ['prefix']

if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    bucket = connect_bucket(key, secret, prefix+'stuff')
    queue = connect_queue(key, secret, prefix+'jobs')
    
    try:
        message = queue.get_messages(visibility_timeout=5)[0]

    except IndexError:
        pass

    else:
        msg = message.get_body()
        logging.info(msg)
        
        if msg.startswith('populate atlas '):
            map_dom = connect_domain(key, secret, prefix+'maps')
            atlas_dom = connect_domain(key, secret, prefix+'atlases')

            populate_atlas(atlas_dom, map_dom, bucket, msg[len('populate atlas '):])
        
        queue.delete_message(message)
