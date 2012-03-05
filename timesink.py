#!/usr/bin/env python3
"""
timesink.py is a program for wasting time while waiting for jobs to complete.
"""

import cherrypy
import collections
import json
import os.path
import sys
import time
import urllib.request
import webbrowser

DEFAULT_SEEN_PATH = os.path.expanduser('~/.timesink')
STOPSIGN = ('http://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/' + 
            'Stop_sign_MUTCD.svg/600px-Stop_sign_MUTCD.svg.png')
STOP_HTML = "<h1>Done</h1><img src='{stop}' />".format(stop=STOPSIGN)
USAGE = """Usage: timesink.py SECONDS [SEEN_FILE]
SECONDS is the number of seconds after which to stop
SEEN_FILE is the file for storing seen images (defaults to ~/.timesink)"""

def get_more_images(seen_path):
    i = 0
    images = collections.OrderedDict()
    tsfile = open(seen_path, 'r')
    already_seen = tsfile.read().strip().split(' ')
    while not images:
        gallery_page = "http://imgur.com/gallery/hot/page/{i}.json".format(i=i)
        response = urllib.request.urlopen(gallery_page)
        result = json.loads(response.readall().decode('utf8'))
        for x in result['gallery']:
            images[x['hash']] = (x['title'], x['ext'])
            for x in already_seen:
                if x in images: del images[x]
            i += 1
    tsfile.close()
    return images

def should_terminate(start_time, stop_time):
    return time.time() - start_time > stop_time

def generate_images(images, seen_file, start_time, stop_time):
    for k, v in images.items():
        if should_terminate(start_time, stop_time): break
        seen_file.write(' ' + k)
        seen_file.flush()
        yield """
            <h1>{title}</h1>
            <img src='http://i.imgur.com/{hash}{extension}' width='800px'>
            """.format(title=v[0], hash=k, extension=v[1])
    while True: yield STOP_HTML

PATH = os.path.abspath(os.path.dirname(__file__))
cherrypy.config.update({'tools.staticdir.on': True,
                        'tools.staticdir.dir': PATH,
                        'tools.staticdir.index': 'index.html',
                       })

class Timesink(object):
    @cherrypy.expose
    def image(self):
        return next(image_generator)

argc = len(sys.argv)
if argc < 2 or argc > 3:
    print(USAGE)
    exit()
elif argc == 2:
    stop_time = int(sys.argv[1])
    seen_path = DEFAULT_SEEN_PATH    
elif argc == 3:
    stop_time = int(sys.argv[1])
    seen_path = sys.argv[2]

start_time = time.time()
images = get_more_images(seen_path)
seen_file = open(seen_path, 'a')
image_generator = generate_images(images, seen_file, start_time, stop_time)
webbrowser.open('http://localhost:8080')    
cherrypy.quickstart(Timesink())