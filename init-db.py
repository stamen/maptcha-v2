from sys import argv

from boto import connect_sdb, connect_s3

if __name__ == '__main__':

    key, secret, prefix = argv[1:]

    sdb = connect_sdb(key, secret)
    s3 = connect_s3(key, secret).get_bucket(prefix+'stuff')
    
    print 'Cleaning out s3', prefix+'stuff'
    
    for key in s3.list():
        key.delete()
    
    for table in (prefix+'atlases', prefix+'maps'):
    
        print 'Cleaning out simpleDB', table
        
        try:
            sdb.delete_domain(table)
        except:
            pass

        sdb.create_domain(table)
