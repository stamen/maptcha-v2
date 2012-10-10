from os import environ
import logging

from util import connect_domain, connect_queue, connect_bucket
from populate_atlas import populate_atlas

key, secret, prefix = environ['key'], environ['secret'], environ['prefix']

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
