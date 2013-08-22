import db
import flask
import json
import platform

server = flask.Flask(__name__)
@server.route('/')
def hello():
    return "Hello"

@server.route('/sprinklers/')
def sprinklers():
    sprinklers = platform.get_sprinklers()
    return json.dumps(data, sort_keys=True), 200, {'Content-Type': 'text/json'}
    
def run(config):
    server.run()
