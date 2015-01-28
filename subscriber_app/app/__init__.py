__author__ = 'ishaan'
from flask import Flask, render_template, send_file
from flask_sockets import Sockets
import redis
import gevent

app = Flask(__name__)
socket = Sockets(app)

r = redis.Redis()


class Subscribers():
    def __init__(self):
        self.subscribers = []
        self.pubsub = r.pubsub()
        self.pubsub.subscribe('airwoot')

    def register(self, client):
        self.subscribers.append(client)

    def _iter_data(self):
        for msg in self.pubsub.listen():
            data = msg.get('data')
            if msg['type'] == 'message':
                yield data

    def send(self, client, message):
        try:
            client.send(message)
        except Exception:
            if client in self.subscribers:
                self.subscribers.remove(client)

    def run(self):
        for data in self._iter_data():
            for client in self.subscribers:
                gevent.spawn(self.send, client, data)

    def start(self):
        gevent.spawn(self.run)


s = Subscribers()
s.start()


@app.route('/')
def index():
    return send_file('templates/index.html')


@socket.route('/sub')
def publish(ws):
    s.register(ws)
    while not ws.closed:
        gevent.sleep()


@app.route('/info')
def info():
    return str(len(s.subscribers))