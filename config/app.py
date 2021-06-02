from gevent import monkey; monkey.patch_all()
from psycogreen.gevent import patch_psycopg; patch_psycopg()

import os
import signal

import gevent
from gevent.pywsgi import WSGIServer
from django.core.wsgi import get_wsgi_application

server = WSGIServer(('0.0.0.0', int(os.environ['PORT'])), get_wsgi_application())
gevent.signal_handler(signal.SIGTERM, server.stop)

server.serve_forever()
gevent.get_hub().join()  # Finish in-flight requests and background tasks
