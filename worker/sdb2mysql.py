from util import connect_domain, get_config_vars
from json import dumps

key, secret, prefix, mysql_hostname, mysql_username, mysql_database, mysql_password, mysql_port = get_config_vars('.')
map_dom = connect_domain(key, secret, prefix+'maps')
atlas_dom = connect_domain(key, secret, prefix+'atlases')
place_dom = connect_domain(key, secret, prefix+'rough_placements')

def does_exist(m,k):
    if k not in m:
        m[k] = ''
    return m[k]
    
def quote_string(value):
    return "'%s'" % value.replace("'", "\'")

if __name__ == '__main__':

    print 'TRUNCATE placements;'

    for place in place_dom.select('select * from `%s`' % place_dom.name):
        
        cols = ['map', 'timestamp', 'ul_lat', 'ul_lon', 'lr_lat', 'lr_lon']
        vals = [quote_string(place[key]) for key in cols]
        
        # update to reflect "map_id" in MySQL.
        cols[0] = 'map_id'

        print 'INSERT INTO placements (%s) VALUES (%s);' % (', '.join(cols), ', '.join(vals))

    print 'TRUNCATE maps;'

    for map in map_dom.select('select * from `%s`' % map_dom.name):
        cols, vals = ['id'], [quote_string(map.name)]
        
        cols += ['atlas', 'image_url', 'image', 'large', 'thumb', 'tiles', 'ul_lat']
        cols += ['ul_lon', 'lr_lat', 'lr_lon', 'aspect', 'status']
        vals += [quote_string(does_exist(map,key)) for key in cols[1:]]
        
        # update to reflect "atlas_id" in MySQL.
        cols[1] = 'atlas_id' 
        # update to reflect "original" in MySQL. 
        cols[2] = 'original'
        
        extras = dict([(key, map[key]) for key in map if key not in cols])

        cols.append('extras_json')
        vals.append(quote_string(dumps(extras)))
        
        print 'INSERT INTO maps (%s) VALUES (%s);' % (', '.join(cols), ', '.join(vals))

    print 'TRUNCATE atlases;'

    for atlas in atlas_dom.select('select * from `%s`' % atlas_dom.name):
        cols, vals = ['id'], [quote_string(atlas.name)]
        
        cols += ['href', 'status', 'timestamp', 'title', 'affiliation', 'map_count']
        vals += [quote_string(atlas[key]) for key in cols[1:]]
        
        print 'INSERT INTO atlases (%s) VALUES (%s);' % (', '.join(cols), ', '.join(vals))
