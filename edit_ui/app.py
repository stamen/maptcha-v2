import logging
from os import environ
from os.path import dirname
from ConfigParser import RawConfigParser

from flask import Flask, request, redirect, render_template, jsonify, config

from util import connect_domain, connect_queue, find_config_file

try:
    config = RawConfigParser()
    config.read(find_config_file(dirname(__file__)))

except TypeError, e:
    logging.critical('Missing configuration file "config.ini"')
    raise

try:
    aws_key = config.get('amazon', 'key')
    aws_secret = config.get('amazon', 'secret')
    aws_prefix = config.get('amazon', 'prefix')

except Exception, e:
    logging.critical('Bad/incomplete configuration file "config.ini"')
    raise

app = Flask(__name__)

@app.route('/')
def index():
    '''
    '''
    return render_template('index.html')

@app.route('/thing/<path:path>')
def thing(path):
    '''
    '''
    bucket = aws_prefix+'stuff'
    return redirect('http://%(bucket)s.s3.amazonaws.com/%(path)s' % locals())

@app.route('/place-rough/map/<id>')
def place_rough_map(id):
    '''
    '''
    map_dom = connect_domain(aws_key, aws_secret, aws_prefix+'maps')
    
    map = map_dom.get_item(id)
    
    return render_template('place-rough-map.html', map=map)

@app.route('/place-rough/atlas/<id>')
def place_rough_atlas(id):
    '''
    '''
    map_dom = connect_domain(aws_key, aws_secret, aws_prefix+'maps')

    q = 'select * from `%s` where atlas = "%s" limit 1' % (map_dom.name, id)
    map = map_dom.select(q).next()
    
    return redirect('/place-rough/map/%s' % map.name)

@app.route('/atlases')
def get_atlases():
    '''
    '''
    atlas_dom = connect_domain(aws_key, aws_secret, aws_prefix+'atlases')

    q = 'select status from `%s` where status="uploaded"' % atlas_dom.name
    
    atlases = [dict(status=a['status'], name=a.name, rough_href='/place-rough/atlas/%s' % a.name)
               for a in atlas_dom.select(q)]
    
    return jsonify(dict(atlases=atlases))

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=8080)
