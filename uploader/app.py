from os import environ
from uuid import uuid1
from urllib import urlopen
from csv import DictReader

from flask import Flask, request, redirect, render_template

from util import connect_domain, connect_queue

app = Flask(__name__)

def create_atlas(domain, queue, url):
    '''
    '''
    row = DictReader(urlopen(url)).next()
    
    if 'address' not in row:
        raise ValueError('Missing "address" in %(url)s' % locals())
    
    #
    # Add an entry for the atlas to the atlases table.
    #
    atlas = domain.new_item(str(uuid1()))
    atlas['href'] = url
    atlas['status'] = 'empty'
    atlas.save()
    
    #
    # Queue the atlas for processing.
    #
    message = queue.new_message('populate atlas %s' % atlas.name)
    queue.write(message)
    
    return atlas.name

@app.route('/')
def index():
    '''
    '''
    return render_template('index.html')

@app.route('/atlas', methods=['POST'])
def post_atlas(id=None):
    '''
    '''
    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']
    dom = connect_domain(key, secret, prefix+'atlases')
    queue = connect_queue(key, secret, prefix+'jobs')

    id = create_atlas(dom, queue, request.form['url'])
    
    return redirect('/atlas/%s' % id, code=303)

@app.route('/atlas/<id>')
def get_atlas(id):
    '''
    '''
    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']
    dom = connect_domain(key, secret, prefix+'atlases')
    
    return repr(dom.get_item(id))

if __name__ == '__main__':
    app.debug = True
    app.run(host='127.0.0.1', port=8080)
