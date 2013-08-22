from flask import Flask

server = Flask(__name__)
@server.route('/')
def hello():
    return "Hello"

def run(config):
    server.run()
