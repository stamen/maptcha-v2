from os import environ
from os.path import dirname, join
from mimetypes import guess_type

from flask import Flask, request, redirect, render_template, make_response

from util import connect_domain, connect_queue
from data import create_atlas

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
    bucket = environ['prefix']+'stuff'
    return redirect('http://%(bucket)s.s3.amazonaws.com/%(path)s' % locals())

@app.route('/atlas', methods=['POST'])
def post_atlas(id=None):
    '''
    '''
    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']
    atlas_dom = connect_domain(key, secret, prefix+'atlases')
    queue = connect_queue(key, secret, prefix+'jobs')

    id = create_atlas(atlas_dom, queue, request.form['url'])
    
    return redirect('/atlas/%s' % id, code=303)

@app.route('/atlas/<id>')
def get_atlas(id):
    '''
    '''
    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']
    atlas_dom = connect_domain(key, secret, prefix+'atlases')
    map_dom = connect_domain(key, secret, prefix+'maps')

    atlas = atlas_dom.get_item(id)
    maps = map_dom.select("select * from `%s` where atlas = '%s'" % (map_dom.name, atlas.name))
    
    return render_template('atlas.html', atlas=atlas, maps=maps)

@app.route('/static/<path:path>')
def static(filename):
    '''
    '''
    path = join(dirname(__file__), 'static')

    body = open(path+'/'+filename).read()
    resp = make_response(body, 200)
    resp.headers['Content-Type'] = guess_type(filename)[0]
    return resp  
    
if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=8080)
