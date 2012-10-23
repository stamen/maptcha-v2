from os import environ
from os.path import dirname, join
from mimetypes import guess_type 


from flask import Flask, request, redirect, render_template, make_response

from util import connect_domain, connect_queue, get_config_vars

app = Flask(__name__) 
key, secret, prefix = get_config_vars(dirname(__file__))

@app.route('/thing/<path:path>')
def thing(path):
    '''
    '''
    bucket = prefix+'stuff'
    return redirect('http://%(bucket)s.s3.amazonaws.com/%(path)s' % locals())

@app.route('/error')
def error():
    '''
    '''
    return render_template('error.html')


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
