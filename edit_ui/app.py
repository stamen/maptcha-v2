from os import environ
from os.path import dirname, join
from mimetypes import guess_type

from flask import Flask, request, redirect, render_template, jsonify, make_response

from util import connect_queue, get_config_vars
from data import connect_domains

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

def place_rough_map(id):
    '''
    '''
    map = map_dom.get_item(id)
    
    if request.method == 'POST':
        return redirect('/place-rough/map/%s' % map.name, code=303)

    return render_template('place-rough-map-alt.html', map=map)

def place_rough_atlas(id):
    '''
    '''
    q = 'select * from `%s` where atlas = "%s" limit 1' % (map_dom.name, id)
    map = map_dom.select(q).next()
    
    return redirect('/place-rough/map/%s' % map.name)

def get_atlases():
    '''
    '''
    q = 'select status from `%s` where status="uploaded"' % atlas_dom.name
    
    atlases = [dict(status=a['status'], name=a.name, rough_href='/place-rough/atlas/%s' % a.name)
               for a in atlas_dom.select(q)]
    
    return jsonify(dict(atlases=atlases))

app = Flask(__name__)

app.add_url_rule('/thing/<path:path>', 'thing', thing)
app.add_url_rule('/static/<path:path>', 'static', static)
app.add_url_rule('/place-rough/map/<id>', 'get/post map rough placement', place_rough_map, methods=['GET', 'POST'])
app.add_url_rule('/place-rough/atlas/<id>', 'get atlas rough placement', place_rough_atlas)
app.add_url_rule('/atlases', 'get atlases', get_atlases)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
