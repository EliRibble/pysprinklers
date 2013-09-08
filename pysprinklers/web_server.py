import db
import flask
import json
import platform

server = flask.Flask(__name__)
@server.route('/')
def root():
    with open('webserver/index.html') as p:
        return p.read()

@server.route('/sprinklers/')
def sprinklers():
    sprinklers = platform.get_sprinklers()
    return json.dumps(data, sort_keys=True), 200, {'Content-Type': 'text/json'}
    
def run(config):
    server.run()
