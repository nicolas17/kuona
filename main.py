# -*- coding: utf-8 -*-

# This file is part of Kuona - crowdsourcing application for OSM HOT
#
# Copyright (c) 2013 Nicolás Alvarez
#
# This program is free software; see the LICENSE file for details.

from jinja2 import Template, Environment, FileSystemLoader, Markup
from cgi import parse_qs
import psycopg2
import tileutils
import random

conn = psycopg2.connect(database="nicolas")

jinja_env = Environment(loader=FileSystemLoader("."))

def encodeToUtf8(iterable):
    return (chunk.encode('utf-8') for chunk in iterable)

global_counter=0

def handler(environ, start_response):
    global global_counter
    start_response("200 OK", [('Content-Type','text/html')])

    data = {}
    data['got_tile']=False

    cur = conn.cursor()
    if environ['REQUEST_METHOD'] == 'POST':
        # handle the response
        formdata = parse_qs(environ['wsgi.input'].read(int(environ['CONTENT_LENGTH'])))
        def getint(key):
            return int(formdata[key][0])
        tilex = getint('tilex')
        tiley = getint('tiley')
        zoom = getint('zoom')

        subtile=None
        for i in (0,1,2,3):
            if 'click%d.x'%i in formdata:
                subtile=i
                break
        if subtile is not None:
            clickx = getint('click%d.x' % i)
            clicky = getint('click%d.y' % i)
            if subtile & 1:
                clickx += 256
            if subtile & 2:
                clicky += 256
            lat,lon = tileutils.tms2latlon(tilex+clickx/512.0, tiley+clicky/512.0, zoom)
            print "village found on tile {},{}, location <{},{}>".format(tilex,tiley,lat,lon)
            cur.execute("INSERT INTO found_villages(lat,lon) VALUES(%s,%s)", (lat,lon))
            cur.execute("UPDATE tiles SET hitcount=hitcount+1 WHERE x=%s AND y=%s AND zoom=%s", (tilex, tiley, zoom));
        elif 'nothing' in formdata:
            pass
            #print "nothing found on tile %d,%d" % (tilex,tiley)
        cur.execute("UPDATE tiles SET seencount=seencount+1 WHERE x=%s AND y=%s AND zoom=%s", (tilex, tiley, zoom));
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM tiles WHERE seencount=0");
    row = cur.fetchone()
    if row is not None and row[0] > 0:
        data['remaining'] = row[0]
    else:
        cur.execute("SELECT COUNT(*) FROM tiles WHERE seencount=1");
        row = cur.fetchone()
        if row is not None and row[0] > 0:
            #data['remaining'] = row[0]
            data['confirmation'] = True

    global_counter+=1
    if False:
        print "looking for a hit tile"
        cur.execute("SELECT x,y,zoom FROM tiles WHERE hitcount between 1 and 3 and seencount in (1,2) order by random() LIMIT 1")
    else:
        print "looking for an unseen tile"
        cur.execute("SELECT x,y,zoom FROM tiles WHERE seencount < 2 order by seencount, random() LIMIT 1")

    row = cur.fetchone()
    if row is not None:
        data['got_tile'] = True
        print row
        x,y,zoom = row
        quadkey = tileutils.tms2quad(x,y,zoom)
        data['tile_src'] = ["http://ecn.t{subtile}.tiles.virtualearth.net/tiles/a{quadkey}{subtile}.jpeg?g=1145".format(quadkey=quadkey,subtile=i) for i in (0,1,2,3)]
        data['tilex'] = x
        data['tiley'] = y
        data['zoom'] = zoom

    conn.commit()
    cur.close()
    template = jinja_env.get_template("main.html")
    return encodeToUtf8(template.generate(data))

def error_404(environ, start_response):
    start_response("404 Not Found", [('Content-Type', 'text/plain')])
    yield "Not found\n"

def app(environ, start_response):
    if environ['PATH_INFO'] == '/':
        return handler(environ, start_response)
    else:
        return error_404(environ, start_response)

def run(app):
    from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
    httpd = WSGIServer(('127.0.0.1', 8080), WSGIRequestHandler)
    httpd.set_app(app)
    print "Serving HTTP on %s port %s ..." % httpd.socket.getsockname()
    httpd.serve_forever()

if __name__ == "__main__":
    run(app)
