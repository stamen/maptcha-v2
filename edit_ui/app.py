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
from data import connect_domains, place_roughly, choose_map, create_atlas  
from relative_time import timesince

aws_key, aws_secret, aws_prefix = get_config_vars(dirname(__file__))

atlas_dom, map_dom, roughplace_dom \
    = connect_domains(aws_key, aws_secret, aws_prefix)

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
            pass
        
        else:
            raise Exception('Mission or invalid "action"')
        
        next_map_id = choose_map(mysql, atlas_id=map['atlas_id'], skip_map_id=map['id'])
        
        conn.close()
        
        return redirect('/place-rough/map/%s' % next_map_id, code=303)
    
    conn.close()
    
    return render_template('place-rough-map.html', map=map, atlas=atlas)

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

    if atlas:
        return render_template('atlas.html', atlas=atlas, maps=maps)

    else:
        abort(404)

def get_atlases():
    '''
    '''
    conn = mysql_connection()
    mysql = conn.cursor(cursor_class=MySQLCursorDict)
    
    mysql.execute('''SELECT id, status, CONCAT("/place-rough/atlas/", id) AS rough_href
                     FROM atlases WHERE status="uploaded"''')

    atlases = mysql.fetchdicts()
    
    conn.close()

    response = make_response(jsonify(dict(atlases=atlases)))
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

def home():
    """
    items = map_dom.select('select tiles from `%s` where image is not null order by image desc' % map_dom.name)
    
    locations = []
    loc_names = ['lr_lon','lr_lat','ul_lon','ul_lat']
    for item in items:
        map = map_dom.get_item(item.name)
        if map:
            for loc_name in loc_names:
                if loc_name in map:
                    locations.append(map[loc_name])

    """
    
        
    return render_template('home.html')


def faq():
    return render_template('faq.html')   

def faq_public():
    return render_template('faq-public.html')

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
app.add_url_rule('/atlases-list', 'get atlases list', get_atlases_list)
app.add_url_rule('/maps-list', 'get maps list', get_maps_list)
app.add_url_rule('/check-map-status/<id>', 'get map status', check_map_status, methods=['GET']) 
app.add_url_rule('/tile/<path:path>', 'tile', tile) 
app.add_url_rule('/home', 'home', home) 
app.add_url_rule('/faq', 'faq', faq) 
app.add_url_rule('/faq-public', 'faq-public', faq_public)

app.error_handler_spec[None][404] = page_not_found

app.add_template_filter(sumiter)
app.add_template_filter(datetimeformat)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
