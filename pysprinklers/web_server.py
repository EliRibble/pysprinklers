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
    return json.dumps(sprinklers, sort_keys=True), 200, {'Content-Type': 'text/json'}
 
@server.route('/sprinklers/<sprinkler_id>/')   
def sprinkler(sprinkler_id):
    return "Hey {0}".format(sprinkler_id)

def run(config):
    server.run()
