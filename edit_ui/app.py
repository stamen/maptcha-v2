from os import environ
from os.path import dirname
from mimetypes import guess_type

from flask import Flask, request, redirect, render_template, jsonify, make_response

from util import connect_domain, connect_queue, get_config_vars

aws_key, aws_secret, aws_prefix = get_config_vars(dirname(__file__))
atlas_dom = connect_domain(aws_key, aws_secret, aws_prefix+'atlases')
map_dom = connect_domain(aws_key, aws_secret, aws_prefix+'maps')

def thing(path):
    '''
    '''
    bucket = aws_prefix+'stuff'
    return redirect('http://%(bucket)s.s3.amazonaws.com/%(path)s' % locals())

def static(filename):
    '''
    '''
    body = open('static/'+filename).read()
    resp = make_response(body, 200)
    resp.headers['Content-Type'] = guess_type(filename)[0]
    return resp

def place_rough_map(id):
    '''
    '''
    map = map_dom.get_item(id)
    
    return render_template('place-rough-map.html', map=map)

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
app.add_url_rule('/place-rough/map/<id>', 'get map rough placement', place_rough_map)
app.add_url_rule('/place-rough/atlas/<id>', 'get atlas rough placement', place_rough_atlas)
app.add_url_rule('/atlases', 'get atlases', get_atlases)

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=8080)
