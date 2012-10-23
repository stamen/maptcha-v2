import logging
from ConfigParser import RawConfigParser
from os.path import realpath, dirname, join, exists

import httplib
import urlparse

#from boto.sdb import regions
from boto import connect_sdb, connect_sqs

def connect_domain(key, secret, name):
    ''' Return a connection to a simpledb domain for atlases.
    '''
    #reg = [reg for reg in regions() if reg.name == 'us-west-1'][0]
    sdb = connect_sdb(key, secret) #, region=reg)
    domain = sdb.get_domain(name)
    
    return domain

def connect_queue(key, secret, name):
    '''
    '''
    sqs = connect_sqs(key, secret)
    queue = sqs.get_queue(name)
    
    return queue

def find_config_file(dir):
    '''
    '''
    dir = realpath(dir)
    
    while True:
        path = join(dir, 'config.ini')
        
        if exists(path):
            return path
        
        if dir == '/':
            break
        
        dir = dirname(dir)
    
    return None

def get_config_vars(dir):
    '''
    '''
    try:
        config = RawConfigParser()
        config.read(find_config_file(dir))
    
    except TypeError, e:
        logging.critical('Missing configuration file "config.ini"')
        raise
    
    try:
        aws_key = config.get('amazon', 'key')
        aws_secret = config.get('amazon', 'secret')
        aws_prefix = config.get('amazon', 'prefix')
    
    except Exception, e:
        logging.critical('Bad/incomplete configuration file "config.ini"')
        raise
    
    return aws_key, aws_secret, aws_prefix


def get_server_status_code(url):
    """
    Download just the header of a URL and
    return the server's status code.
    """
    # http://stackoverflow.com/questions/1140661
    host, path = urlparse.urlparse(url)[1:3]    # elems [1] and [2]
    try:
        conn = httplib.HTTPConnection(host)
        conn.request('HEAD', path)
        return conn.getresponse().status
    except StandardError:
        return None

def check_url(url):
    """
    Check if a URL exists without downloading the whole file.
    We only check the URL header.
    """
    # see also http://stackoverflow.com/questions/2924422
    good_codes = [httplib.OK, httplib.FOUND, httplib.MOVED_PERMANENTLY]
    return get_server_status_code(url) in good_codes 