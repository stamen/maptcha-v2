from os import environ
from os.path import dirname, join
from mimetypes import guess_type 
import time,datetime

from PIL import Image
from PIL.ImageStat import Stat
from StringIO import StringIO
from urllib import urlopen, quote_plus

from flask import Flask, request, redirect, render_template, jsonify, make_response, abort
from mysql.connector import connect, cursor

from util import connect_queue, get_config_vars, get_all_records
from data import place_roughly, choose_map, create_atlas  
from relative_time import timesince

aws_key, aws_secret, aws_prefix = get_config_vars(dirname(__file__))

queue = connect_queue(aws_key, aws_secret, aws_prefix+'jobs')

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

def thing(path):
    '''
    '''
    bucket = aws_prefix+'stuff' 
    
    # URL encode path, because S3 URL's are encoded
    path = quote_plus(path,safe="/")
    
    return redirect('http://%(bucket)s.s3.amazonaws.com/%(path)s' % locals())

def static(filename):
    '''
    '''
    path = join(dirname(__file__), 'static')
    
    body = open(path+'/'+filename).read()
    resp = make_response(body, 200)
    resp.headers['Content-Type'] = guess_type(filename)[0]
    return resp

def index():
    '''
    will want to do this filtered for client
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)

    # get number of atlases and last-updated time
    mysql.execute('SELECT COUNT(id), MAX(timestamp) FROM atlases')
    (atlas_count, latest) = mysql.fetchone()

    # get map numbers
    mysql.execute('''SELECT COUNT(id), SUM(IF(status = 'placed-roughly', 1, 0)) FROM maps''')
    total, placed = mysql.fetchone()
    map_totals = dict(total=total, placed=placed)

    return render_template('index.html', latest=latest, atlas_count=atlas_count, maps=map_totals) 

def upload():
    '''
    '''
    return render_template('upload.html') 

def place_rough_map(id):
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)

    # get atlas, supplies edit ui w/ hints
    mysql.execute('SELECT * FROM maps WHERE id = %s', (id, ))
    map = mysql.fetchdict()
    
    if not map:
        abort(404) 
    
    # get atlas, supplies edit ui w/ hints
    atlas_id = map['atlas']
    mysql.execute('SELECT * FROM atlases WHERE id = %s', (map['atlas_id'], ))
    atlas = mysql.fetchdict()

    if request.method == 'POST':
                
        if request.form.get('action', None) == 'place':
            #
            # Expect four floating point values from a submitted form: ul_lat,
            # ul_lon, lr_lat, and lr_lon corresponding to the four corners of the
            # roughly-placed map. Make a note of the new placement and respond
            # with a 303 redirect to send the submitter someplace useful.
            #
            ul_lat = float(request.form.get('ul_lat', None))
            ul_lon = float(request.form.get('ul_lon', None))
            lr_lat = float(request.form.get('lr_lat', None))
            lr_lon = float(request.form.get('lr_lon', None))
            
            place_roughly(mysql, queue, map, ul_lat, ul_lon, lr_lat, lr_lon)
        
        elif request.form.get('action', None) == 'skip':
            # counting number of times the map has been skipped, possibly to track bad maps
            if 'skip_map' in map:
                skip_map_ct = int(map['skip_map']) + 1
            else:
                skip_map_ct = 1
            
            map['skip_map'] = skip_map_ct
            map.save()
        
        else:
            raise Exception('Mission or invalid "action"')
        
        next_map = choose_map(mysql, atlas_id=map['atlas_id'], skip_map_id=map['id'])
        return redirect('/place-rough/map/%s' % next_map['id'], code=303) 
    
    # cookies to check if you've placed all maps in atlas
    # maps_remaining will return 0 when on last map
    cookie_id = '__%s_atlas_%s' % (aws_prefix,atlas_id)
    maps_cookie = request.cookies.get(cookie_id) 
    if maps_cookie:
        maps_cookie = maps_cookie.split("|")
        if map.name not in maps_cookie:
            maps_cookie.append(map.name)
    else:
        maps_cookie = [map.name] 
    
    maps_remaining = int(atlas['map_count']) - len(maps_cookie)
    
    resp = make_response( render_template('place-rough-map.html', map=map, atlas=atlas, maps_remaining=maps_remaining) )
    resp.set_cookie(cookie_id, "|".join(maps_cookie))
    return resp
    
    #return render_template('place-rough-map.html', map=map, atlas=atlas,maps_cookie=maps_cookie)

def place_rough_atlas(id):
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)

    map_id = choose_map(mysql, atlas_id=id)
    
    conn.close()

    return redirect('/place-rough/map/%s' % map_id)

def post_atlas(id=None):
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)

    # wrap in try/catch ???
    rsp = create_atlas(mysql, queue, request.form['url'], request.form['atlas-name'], request.form['atlas-affiliation'])
    
    conn.close()

    if 'error' in rsp:
        return render_template('error.html',msg=rsp)
    elif 'success' in rsp:
        return redirect('/atlas-hints/%s' % rsp['success'].name, code=303)
    
    return render_template('error.html', msg={'error':'unknown'}) 

# simple 404 page
def page_not_found(error):
    return render_template('404.html'),404
       
def post_atlas_hints(id=None): 
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)

    mysql.execute('SELECT * FROM atlases WHERE id = %s', (id, ))
    atlas = mysql.fetchdict()
    
    if atlas:
        if request.method == 'POST': 
        
            ul_lat = float(request.form.get('ul_lat', None))
            ul_lon = float(request.form.get('ul_lon', None))
            lr_lat = float(request.form.get('lr_lat', None))
            lr_lon = float(request.form.get('lr_lon', None))
            has_features = bool(request.form.get('hints_features', False))
            has_cities = bool(request.form.get('hints_cities', False))
            has_streets = bool(request.form.get('hints_streets', False))
        
        
            atlas['ul_lat'] = '%.8f' % ul_lat
            atlas['ul_lon'] = '%.8f' % ul_lon
            atlas['lr_lat'] = '%.8f' % lr_lat
            atlas['lr_lon'] = '%.8f' % lr_lon 
            atlas['hint_features'] = has_features
            atlas['hint_cities'] = has_cities
            atlas['hint_streets'] = has_streets
        
            atlas.save()
        
            return redirect('/atlas/%s' % atlas.name, code=303)

        return render_template('atlas-hints.html', atlas=atlas)
    else:
        abort(404)


def get_map(id):
    '''
    ''' 
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('SELECT * FROM maps WHERE id = %s', (id, ))
    
    map = mysql.fetchdict()
    
    conn.close()
    
    if map:
        return render_template('map.html', map=map)
    else:
        abort(404)
        
def get_atlas(id):
    '''
    ''' 
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('SELECT * FROM atlases WHERE id = %s', (id, ))
    atlas = mysql.fetchdict()
    
    if atlas:
        mysql.execute('SELECT * FROM maps WHERE atlas_id = %s', (atlas['id'], ))
        maps = mysql.fetchdicts()
        
        conn.close()
        
        has_tiles = bool([True for map in maps if map['tiles']])
    
        return render_template('atlas.html', atlas=atlas, maps=maps, has_tiles=has_tiles)
    else:
        conn.close()
        abort(404)

def get_atlases():
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('''SELECT id, status, CONCAT("/place-rough/atlas/", id) AS rough_href
                     FROM atlases WHERE status="uploaded"''')

    atlases = [dict(status=a['status'], id=a['id'], rough_href='/place-rough/atlas/%(id)s' % a, geo={'tile_template':'/tile/atlas/%(id)s/{Z}/{X}/{Y}.png' % a, 'map_sandwich': '/map-sandwich/atlas/%(id)s' % a})
               for a in mysql.fetchdicts()]

    conn.close()

    response = make_response(jsonify(dict(atlases=atlases)))
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response 
    
def get_maps():
    '''
    '''
    q = 'select status,tiles,version,atlas from `%s` where status!="processing"' % map_dom.name
    maps = []
    bucket = aws_prefix+'stuff' 
    url = 'http://%(bucket)s.s3.amazonaws.com/maps' % locals()

    for m in map_dom.select(q):
        obj = {}
        
        obj['status'] = m['status']
        obj['name'] = m.name
        obj['atlas'] = m['atlas'] 
        obj['rough_href'] = '/place-rough/map/%s' % m.name  
        
        obj['geo'] = {}
        
        if 'tiles' in m:
            obj['geo']['vrt'] =  '/thing/maps/%s/image.vrt' %(m.name)
            obj['geo']['tile_template'] = '/tile/map/%s/{Z}/{X}/{Y}.png' %(m.name)
            obj['geo']['tile_template_full'] = '/thing/maps/%s/%s/{Z}/{X}/{Y}.png' %(m.name,m['tiles'])
            obj['geo']['map_sandwich'] = '/map-sandwich/map/%s' %(m.name)
        else:
            pass
            
        maps.append(obj)

    response = make_response(jsonify(dict(maps=maps)))
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response

def get_atlases_list():
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('''SELECT *, CONCAT("/place-rough/atlas/", id) AS rough_href
                     FROM atlases WHERE status="uploaded"''')

    atlases = mysql.fetchdicts()
    
    conn.close()

    return render_template('atlases-list.html', atlases=atlases)
    
def get_maps_list():
    '''
    ''' 
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('SELECT * FROM maps')
    
    maps = mysql.fetchdicts()
    
    conn.close()

    return render_template('maps-list.html', maps=maps)
            
def check_map_status(id=None):
    '''
    '''
    if not id:
        return jsonify({'error':'unkown'})
    
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('SELECT id, status FROM maps WHERE atlas_id = %s AND status != "empty"', (id, ))
    
    maps = mysql.fetchdicts()
    
    conn.close()
    
    uploaded = []
    
    for map in maps:
        uploaded.append({'name': map['id'], 'status': map['status']})

    return jsonify({'uploaded': uploaded})
    
def tile(path):
    '''
    ''' 
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    tms_path = '.'.join(path.split('.')[:-1])
    bucket = aws_prefix+'stuff'
    opaque = False
    
    image = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    
    mysql.execute('SELECT id, tiles FROM maps WHERE image IS NOT NULL ORDER BY id DESC')
    
    items = mysql.fetchdicts()
    
    conn.close()

    for item in items:
        if 'tiles' in item:
            s3_path = 'maps/%s/%s/%s.png' % (item['id'], item['tiles'], tms_path)
            url = 'http://%(bucket)s.s3.amazonaws.com/%(s3_path)s' % locals()
        
            try:
                tile_img = Image.open(StringIO(urlopen(url).read()))
            except IOError: 
                continue
        
            fresh_img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
            fresh_img.paste(tile_img, (0, 0), tile_img)
            fresh_img.paste(image, (0, 0), image)
            image = fresh_img
        
        if Stat(image).extrema[3][0] > 0:
            opaque = True         
            break  
    
    if not opaque:
        url = 'http://tile.stamen.com/toner-lite/%s.png' % tms_path
        tile_img = Image.open(StringIO(urlopen(url).read()))
        tile_img.paste(image, (0, 0), image)
        image = tile_img
        

    bytes = StringIO()
    image.save(bytes, 'JPEG')
    
    resp = make_response(bytes.getvalue(), 200)
    resp.headers['Content-Type'] = 'image/jpeg'

    return resp


def tile_by_id(id,path):
    '''
    ''' 
    
    tms_path = '.'.join(path.split('.')[:-1])
    bucket = aws_prefix+'stuff'
    opaque = False
    endpoint = request.endpoint
    
    image = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    
    if request.endpoint == "tilemap": 
        items = map_dom.select("select tiles from `%s` where name = '%s'" % (map_dom.name,id))
    elif request.endpoint == "tileatlas":
        items = map_dom.select("select tiles from `%s` where atlas='%s' and image is not null order by image desc" % (map_dom.name,id))
    
    if items:
        for item in items:
            if 'tiles' in item:
                s3_path = 'maps/%s/%s/%s.png' % (item.name, item['tiles'], tms_path)
                url = 'http://%(bucket)s.s3.amazonaws.com/%(s3_path)s' % locals()
        
                try:
                    tile_img = Image.open(StringIO(urlopen(url).read()))
                except IOError: 
                    continue
        
                fresh_img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
                fresh_img.paste(tile_img, (0, 0), tile_img)
                fresh_img.paste(image, (0, 0), image)
                image = fresh_img
        
            if Stat(image).extrema[3][0] > 0:
                opaque = True         
                break  
    
    if not opaque:
        url = 'http://tile.stamen.com/toner-lite/%s.png' % tms_path
        tile_img = Image.open(StringIO(urlopen(url).read()))
        tile_img.paste(image, (0, 0), image)
        image = tile_img
        

    bytes = StringIO()
    image.save(bytes, 'JPEG')
    
    resp = make_response(bytes.getvalue(), 200)
    resp.headers['Content-Type'] = 'image/jpeg'

    return resp
    
    
def map_sandwich(id=None):
    """
        Probably need to do some verification on if the atlas and/or map exist
    """                                                                       
    
    tpl = '/tile/{Z}/{X}/{Y}.png'
    
    if id is not None:
        if request.endpoint ==  'map-sandwich-map':
            tpl = '/tile/map/%s/{Z}/{X}/{Y}.png' % id
        elif request.endpoint ==  'map-sandwich-atlas':
            tpl = '/tile/atlas/%s/{Z}/{X}/{Y}.png' % id
    
    return render_template('home.html',tpl=tpl)

def faq():
    return render_template('faq.html')   

def faq_public():
    return render_template('faq-public.html')
    
def docs():
    return render_template('docs.html')  

# template filters
def datetimeformat(value, relative=True, format='%b %d, %Y / %I:%M%p'):
    t = datetime.datetime.fromtimestamp(float(value)) 
    if relative:
        return timesince(t)
    else:
        return t.strftime(format)
             
def sumiter(s):
    ''' gets count of iterator
    '''
    return sum(1 for _ in s)
    
app = Flask(__name__)

app.add_url_rule('/thing/<path:path>', 'thing', thing)
app.add_url_rule('/static/<path:path>', 'static', static)
app.add_url_rule('/', 'index', index)
app.add_url_rule('/upload', 'upload', upload)
app.add_url_rule('/place-rough/map/<id>', 'get/post map rough placement', place_rough_map, methods=['GET', 'POST'])
app.add_url_rule('/place-rough/atlas/<id>', 'get atlas rough placement', place_rough_atlas)
app.add_url_rule('/atlases', 'get atlases', get_atlases)
app.add_url_rule('/atlas', 'post atlas', post_atlas, methods=['POST'])
app.add_url_rule('/atlas-hints/<id>', 'post atlas hints', post_atlas_hints, methods=['GET', 'POST'])
app.add_url_rule('/atlas/<id>', 'get atlas', get_atlas)
app.add_url_rule('/map/<id>', 'get map', get_map) 
app.add_url_rule('/maps', 'get maps', get_maps)
app.add_url_rule('/atlases-list', 'get atlases list', get_atlases_list)
app.add_url_rule('/maps-list', 'get maps list', get_maps_list)
app.add_url_rule('/check-map-status/<id>', 'get map status', check_map_status, methods=['GET']) 
app.add_url_rule('/tile/<path:path>', 'tile', tile)

app.add_url_rule('/tile/map/<id>/<path:path>', 'tilemap', tile_by_id)
app.add_url_rule('/tile/atlas/<id>/<path:path>', 'tileatlas', tile_by_id)
 
app.add_url_rule('/map-sandwich', 'map-sandwich', map_sandwich)
app.add_url_rule('/map-sandwich/map/<id>', 'map-sandwich-map', map_sandwich)
app.add_url_rule('/map-sandwich/atlas/<id>', 'map-sandwich-atlas', map_sandwich) 

app.add_url_rule('/faq', 'faq', faq) 
app.add_url_rule('/faq-public', 'faq-public', faq_public)
app.add_url_rule('/docs', 'docs', docs)

app.error_handler_spec[None][404] = page_not_found

app.add_template_filter(sumiter)
app.add_template_filter(datetimeformat)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
