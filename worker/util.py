from boto.sdb import regions
from boto import connect_s3, connect_sdb, connect_sqs

def connect_domain(key, secret, name):
    ''' Return a connection to a simpledb domain for atlases.
    '''
    reg = [reg for reg in regions() if reg.name == 'us-west-1'][0]
    sdb = connect_sdb(key, secret, region=reg)
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