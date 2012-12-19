''' Run me with cron:

# m h  dom mon dow   command
* * * * *   cd yearofthebay && python worker/run.py

'''
from os import environ
from time import time, sleep
import logging    

from os.path import realpath, dirname, join, exists 

from mysql.connector import connect, cursor

from util import connect_queue, connect_bucket, get_config_vars
from populate_atlas import create_atlas_map
from tile_map import generate_map_tiles

key, secret, prefix = get_config_vars(dirname(__file__)) 
#key, secret, prefix = environ['key'], environ['secret'], environ['prefix']

def mysql_connection():
    return connect(user='yotb', password='y0tb', database='yotb_migurski', autocommit=True)

class MySQLCursorDict(cursor.MySQLCursor):
    def fetchdict(self):
        row = self.fetchone()
        if row:
            return dict(zip(self.column_names, row))
        return None
    
    def fetchdicts(self):
        rows = self.fetchall()
        cols = self.column_names
        
        return [dict(zip(cols, row)) for row in rows]

if __name__ == '__main__':

    due = time() + 55
    
    logging.basicConfig(level=logging.INFO)

    bucket = connect_bucket(key, secret, prefix+'stuff')
    queue = connect_queue(key, secret, prefix+'jobs')
    
    while time() < due:
        try:
            message = queue.get_messages(visibility_timeout=5)[0]
    
        except IndexError:
            pass
    
        else:
            msg = message.get_body()
            logging.info(msg)
            
            conn = mysql_connection()
            mysql = conn.cursor(cursor_class=MySQLCursorDict)
        
            if msg.startswith('create map '):
                map_id = msg[len('create map '):]
                create_atlas_map(mysql, bucket, map_id)
            
            if msg.startswith('tile map '):
                map_id = msg[len('tile map '):]
                generate_map_tiles(mysql, bucket, map_id)
            
            queue.delete_message(message)
            
            conn.close()
        
        logging.debug('worker sleeping')
        sleep(5)
