import logging
from ConfigParser import RawConfigParser
from os.path import realpath, dirname, join, exists

#from boto.sdb import regions
from boto import connect_s3, connect_sdb, connect_sqs

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

def connect_bucket(key, secret, name):
    '''
    '''
    s3 = connect_s3(key, secret)
    bucket = s3.get_bucket(name)
    
    return bucket 

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
