from os import environ
from uuid import uuid1
from urllib import urlopen
from csv import DictReader

from boto import connect_sdb, connect_sqs
from boto.exception import SDBResponseError
from flask import Flask, request, render_template

app = Flask(__name__)

def connect_atlases_domain(key, secret, prefix):
    ''' Return a connection to a simpledb domain for atlases.
    '''
    sdb = connect_sdb(key, secret)
    
    try:
        domain = sdb.get_domain(prefix+'atlases')
    except SDBResponseError:
        domain = sdb.create_domain(prefix+'atlases')
    
    return domain

def connect_queue(key, secret, prefix):
    '''
    '''
    sqs = connect_sqs(key, secret)
    queue = sqs.get_queue(prefix+'jobs')
    
    return queue

def post_atlas(domain, queue, url):
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
    atlas['progress'] = 0
    atlas.save()
    
    #
    # Queue the atlas for processing.
    #
    message = queue.new_message('create atlas %s' % atlas.name)
    queue.write(message)

@app.route('/')
def index():
    '''
    '''
    return render_template('index.html')

@app.route('/atlas', methods=['POST'])
def atlas():
    '''
    '''
    key, secret, prefix = environ['key'], environ['secret'], environ['prefix']
    dom = connect_atlases_domain(key, secret, prefix)
    queue = connect_queue(key, secret, prefix)

    post_atlas(dom, queue, request.form['url'])
    
    return 'buuh'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
