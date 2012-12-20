''' Run me with cron:

# m h  dom mon dow   command
* * * * *   cd yearofthebay && python worker/run.py

''' 
from sys import argv
from os import environ
from time import time, sleep
import logging    

from os.path import realpath, dirname, join, exists 

from mysql.connector import connect, cursor

from util import connect_queue, connect_bucket, get_config_vars
from populate_atlas import create_atlas_map
from tile_map import generate_map_tiles

key, secret, prefix, mysql_hostname, mysql_username, mysql_database, mysql_password, mysql_port = get_config_vars(dirname(__file__))

def mysql_connection():
    return connect(user=mysql_username, password=mysql_password, database=mysql_database, port=mysql_port, autocommit=True)

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


def process_queue(queue, msg, bucket):
    
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
    
if __name__ == '__main__': 
    try:
        force_queue = argv[1:][0]
    except IndexError:
        force_queue = None
     
   
    due = time() + 55
    
    logging.basicConfig(level=logging.INFO)

    bucket = connect_bucket(key, secret, prefix+'stuff')
    
    queue_create = connect_queue(key, secret, prefix+'create') 
    queue_tile = connect_queue(key, secret, prefix+'tile')
    
    while time() < due:
        #
        if force_queue == "create":
            message = queue_create.get_messages(visibility_timeout=5)
            if message:
                process_queue(queue_create, message[0], bucket) 
                
        elif force_queue == "tile":
            message = queue_tile.get_messages(visibility_timeout=5)
            if message:
                process_queue(queue_tile, message[0], bucket) 
                
        else:
            message = queue_create.get_messages(visibility_timeout=5)
            if message:
                process_queue(queue_create, message[0], bucket)
            else:
                message = queue_tile.get_messages(visibility_timeout=5)
                if message:
                    process_queue(queue_tile, message[0], bucket)  
                 
        """
        try:
            message = queue_create.get_messages(visibility_timeout=5)[0]
            process_queue(queue_create, message, bucket)
        except IndexError:
            message = queue_tile.get_messages(visibility_timeout=5)[0]
            process_queue(queue_tile, message, bucket)
        except IndexError:
            pass
            
        else:
            pass
            
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
            
            queue_in_use.delete_message(message)
            
            conn.close()
        """
        
        logging.debug('worker sleeping')
        sleep(5)
