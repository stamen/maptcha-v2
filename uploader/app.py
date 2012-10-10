from os import environ
from uuid import uuid1
from urllib import urlopen
from csv import DictReader

from flask import Flask, request, render_template

from util import connect_domain, connect_queue

app = Flask(__name__)

def post_atlas(domain, queue, url):
    '''
    '''
    print 'fuck'
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
    dom = connect_domain(key, secret, prefix+'atlases')
    queue = connect_queue(key, secret, prefix+'jobs')

    post_atlas(dom, queue, request.form['url'])
    
    return 'buuh'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
