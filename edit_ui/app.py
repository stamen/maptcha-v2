from os import environ
from os.path import dirname, join
from mimetypes import guess_type

from flask import Flask, request, redirect, render_template, jsonify, make_response

from util import connect_queue, get_config_vars
from data import connect_domains, place_roughly, choose_map, create_atlas

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
    '''
    atlas_db = aws_prefix+'atlases'
    map_db = aws_prefix+'maps' 
    
    # get number of atlases
    # will want to do this on a per client basis
    atlas_count = atlas_dom.select("select count(*) from `%s`" % atlas_db).next()  
    
    #TODO: get last updated time
    
    #TODO: get recent list of map's for client
    
    return render_template('index.html',atlas_count=atlas_count['Count']) 

def upload():
    '''
    '''
    return render_template('upload.html') 

def place_rough_map(id):
    '''
    '''
    map = map_dom.get_item(id)
    
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

    return render_template('place-rough-map.html', map=map)

def place_rough_atlas(id):
    '''
    '''
    map = choose_map(map_dom, atlas_id=id)
    
    return redirect('/place-rough/map/%s' % map.name)    

def post_atlas(id=None):
    '''
    '''
    queue = connect_queue(aws_key, aws_secret, aws_prefix+'jobs')

    rsp = create_atlas(atlas_dom, map_dom, queue, request.form['url'], request.form['atlas-name'], request.form['atlas-affiliation']) 
    
    if 'error' in rsp:
        return render_template('error.html',msg=rsp)
    elif 'success' in rsp:
        return redirect('/atlas-hints/%s' % rsp['success'].name, code=303)
    
    return render_template('error.html', msg={'error':'unknown'}) 
    
def post_atlas_hints(id=None): 
    '''
    '''
    atlas = atlas_dom.get_item(id,consistent_read=True)
    if request.method == 'POST': 
        
        ul_lat = float(request.form.get('ul_lat', None))
        ul_lon = float(request.form.get('ul_lon', None))
        lr_lat = float(request.form.get('lr_lat', None))
        lr_lon = float(request.form.get('lr_lon', None))
        has_streets = bool(request.form.get('hints-features', False))
        has_cities = bool(request.form.get('hints-citites', False))
        has_streets = bool(request.form.get('hints-streets', False))
        
        
        atlas['ul_lat'] = '%.8f' % ul_lat
        atlas['ul_lon'] = '%.8f' % ul_lon
        atlas['lr_lat'] = '%.8f' % lr_lat
        atlas['lr_lon'] = '%.8f' % lr_lon 
        atlas['hint_features'] = has_streets
        atlas['hint_cities'] = has_cities
        atlas['hint_streets'] = has_streets
        
        atlas.save()
        
        return redirect('/atlas/%s' % atlas.name, code=303)
         
    
    return render_template('upload-placement.html', atlas=atlas)
    
def get_atlas(id):
    '''
    ''' 
    atlas = atlas_dom.get_item(id,consistent_read=True)
    q = "select * from `%s` where atlas = '%s'" % (map_dom.name, atlas.name)
    maps = map_dom.select(q,consistent_read=True)
    
    return render_template('atlas.html', atlas=atlas, maps=maps)

def get_atlases():
    '''
    '''
    q = 'select status from `%s` where status="uploaded"' % atlas_dom.name
    
    atlases = [dict(status=a['status'], name=a.name, rough_href='/place-rough/atlas/%s' % a.name)
               for a in atlas_dom.select(q)]
    
    return jsonify(dict(atlases=atlases)) 
    
def check_map_status(id=None):
    rsp = 'error'
    if id:
        map = map_dom.get_item(id,consistent_read=True)
        if map:
            rsp = map['status']
    
    return jsonify(status=rsp)
  
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
app.add_url_rule('/check-map-status/<id>', 'get map status', check_map_status, methods=['GET'])

app.add_template_filter(sumiter)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
