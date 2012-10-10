from os import environ
from boto import connect_sdb
from boto.exception import SDBResponseError
from flask import Flask, request, render_template

app = Flask(__name__)

def connect_maps_domain(key, secret, prefix):
    ''' Return a connection to a simpledb domain for maps.
    '''
    sdb = connect_sdb(key, secret)
    
    try:
        dom = sdb.get_domain(prefix+'maps')
    except SDBResponseError:
        dom = sdb.create_domain(prefix+'maps')
    
    return dom

def post_map(domain, url):
    '''
    '''
    print domain, url

@app.route('/')
def index():
    '''
    '''
    return render_template('index.html')

@app.route('/map', methods=['POST'])
def map():
    '''
    '''
    dom = connect_maps_domain(environ['key'], environ['secret'], environ['prefix'])
    post_map(dom, request.form['url'])
    
    return 'buuh'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
