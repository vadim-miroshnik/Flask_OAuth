from gevent import monkey

monkey.patch_all()

from gevent.pywsgi import WSGIServer
from app import app

http_server = WSGIServer(("", 8000), app)
http_server.serve_forever()
