from __future__ import unicode_literals

import multiprocessing

bind = "127.0.0.1:%(gunicorn_port)s"
workers = 2
loglevel = "error"
proc_name = "%(proj_name)s"
worker_class = "eventlet"

# def when_ready(server):
#     from django.core.management import call_command
#     call_command('validate')
