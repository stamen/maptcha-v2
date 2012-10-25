from os import environ
from os.path import dirname, join
from mimetypes import guess_type 
import time,datetime

from flask import Flask, request, redirect, render_template, jsonify, make_response, abort

from util import connect_queue, get_config_vars, get_all_records
from data import connect_domains, place_roughly, choose_map, create_atlas  
from relative_time import timesince

aws_key, aws_secret, aws_prefix = get_config_vars(dirname(__file__))

atlas_dom, map_dom, roughplace_dom \
    = connect_domains(aws_key, aws_secret, aws_prefix)

def thing(path):
    '''
    '''
    bucket = aws_prefix+'stuff'
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
    
    # get number of atlases
    atlas_count = atlas_dom.select("select count(*) from `%s`" % atlas_dom.name).next()  
    
    #get last updated time 
    now = time.time()
    latest_query="select timestamp from`%s` where timestamp < '%s' order by timestamp desc limit 1"%(atlas_dom.name,now)
    latest = atlas_dom.select(latest_query,consistent_read=True).next()  
    
    #get recent list of map's for client 
    q = "select * from `%s`"%(map_dom.name)
    maps = get_all_records(map_dom,q)
    
    map_totals = {}
    map_totals['total'] = 0
    map_totals['placed'] = 0
    for map in maps:
        map_totals['total'] += 1
        if 'version' in map:
            map_totals['placed'] += 1
    
    
    return render_template('index.html',latest=latest['timestamp'],atlas_count=atlas_count['Count'],maps=map_totals) 

def upload():
    '''
    '''
    return render_template('upload.html') 

def place_rough_map(id):
    '''
    '''
    map = map_dom.get_item(id) 
    
    # get atlas, supplies edit ui w/ hints
    atlas_id = map['atlas']
    atlas = atlas_dom.get_item(atlas_id)
    
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
            
            place_roughly(map_dom, roughplace_dom, map, ul_lat, ul_lon, lr_lat, lr_lon)
        
        elif request.form.get('action', None) == 'skip':
            pass
        
        else:
            raise Exception('Mission or invalid "action"')
        
        next_map = choose_map(map_dom, atlas_id=map['atlas'], skip_map_id=map.name)
        return redirect('/place-rough/map/%s' % next_map.name, code=303)

    return render_template('place-rough-map.html', map=map, atlas=atlas)

def place_rough_atlas(id):
    '''
    '''
    map = choose_map(map_dom, atlas_id=id)
    
    return redirect('/place-rough/map/%s' % map.name)    

def post_atlas(id=None):
    '''
    '''
    queue = connect_queue(aws_key, aws_secret, aws_prefix+'jobs')
    
    # wrap in try/catch ???
    rsp = create_atlas(atlas_dom, map_dom, queue, request.form['url'], request.form['atlas-name'], request.form['atlas-affiliation']) 
    
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
    atlas = atlas_dom.get_item(id,consistent_read=True)
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
    
def get_atlas(id):
    '''
    ''' 
    atlas = atlas_dom.get_item(id,consistent_read=True)
    if atlas:
        q = "select * from `%s` where atlas = '%s'" % (map_dom.name, atlas.name)
        maps = map_dom.select(q,consistent_read=True)
    
        return render_template('atlas.html', atlas=atlas, maps=maps)
    else:
        abort(404)

def get_atlases():
    '''
    '''
    q = 'select status from `%s` where status="uploaded"' % atlas_dom.name
    
    atlases = [dict(status=a['status'], name=a.name, rough_href='/place-rough/atlas/%s' % a.name)
               for a in atlas_dom.select(q)]
    response = make_response(jsonify(dict(atlases=atlases)))
    response.headers['Access-Control-Allow-Origin'] = "*"
    return response

def get_atlases_list():
    '''
    '''
    q = 'select * from `%s`' % atlas_dom.name 
    atlases = [dict(status=a['status'], name=a.name, affiliation=a.get('affiliation','-'), title=a.get('title',a.name), uploaded=a.get('timestamp',0), maps=a.get('map_count','-'), rough_href='/place-rough/atlas/%s' % a.name)
               for a in atlas_dom.select(q)]

    return render_template('atlases-list.html', atlases=atlases)
    
def get_maps_list(): 
    q = "select * from `%s`"%(map_dom.name)
    maps = get_all_records(map_dom,q)
    return render_template('maps-list.html', maps=maps)
    
            
def check_map_status(id=None):
    rsp = {'error':'unkown'}
    if id:
        #map = map_dom.get_item(id,consistent_read=True)
        q = "select name from `%s` where atlas = '%s' and status = 'finished'"%(map_dom.name,id)
        done = map_dom.select(q,consistent_read=True)
        if done:
            rsp = {'finished':[]}
            for item in done:
                rsp['finished'].append(item.name)
    
    return jsonify(rsp) 
    
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
app.add_url_rule('/atlases-list', 'get atlases list', get_atlases_list)
app.add_url_rule('/maps-list', 'get maps list', get_maps_list)
app.add_url_rule('/check-map-status/<id>', 'get map status', check_map_status, methods=['GET']) 

app.error_handler_spec[None][404] = page_not_found

app.add_template_filter(sumiter)
app.add_template_filter(datetimeformat)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
