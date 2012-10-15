from sys import argv

#from boto.sdb import regions
from boto import connect_sdb, connect_s3, connect_sqs

if __name__ == '__main__':

    key, secret, prefix = argv[1:]

    #reg = [reg for reg in regions() if reg.name == 'us-west-1'][0]
    sdb = connect_sdb(key, secret) #, region=reg)
    sqs = connect_sqs(key, secret)
    s3 = connect_s3(key, secret)
    
    # table = prefix+'rough_placements'
    # print 'Creating simpleDB domain', table
    # sdb.create_domain(table)
    # exit()
    
    print 'Cleaning out s3', prefix+'stuff'
    
    try:
        bucket = s3.get_bucket(prefix+'stuff')
    
    except:
        # nonexistent bucket
        bucket = s3.create_bucket(prefix+'stuff')
    
    else:
        # bucket exists
        for key in bucket.list():
            key.delete()
    
    for suffix in ('maps', 'atlases', 'rough_placements'):
    
        table = prefix+suffix
        print 'Cleaning out simpleDB', table
        
        try:
            domain = sdb.get_domain(table)

        except:
            # nonexistent domain
            sdb.create_domain(table)
        
        else:
            # domain exists
            for item in domain.select('select * from `%s`' % table):
                item.delete()
    
    print 'Cleaning out queue', prefix+'jobs'
    
    queue = sqs.get_queue(prefix+'jobs')
    
    while True:
        messages = queue.get_messages(1)
        
        if not messages:
            break

        queue.delete_message(messages[0])
