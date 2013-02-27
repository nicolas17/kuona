# -*- coding: utf-8 -*-

# This file is part of Kuona - crowdsourcing application for OSM HOT
#
# Copyright (c) 2013 Nicolás Alvarez
#
# This program is free software; see the LICENSE file for details.

import math

def tms2quad(x,y,zoom):
    quadkey=""
    for i in reversed(range(0,zoom)):
        num = 0
        mask = 1<<i
        if x & mask:
            num |= 1
        if y & mask:
            num |= 2
        quadkey += str(num)

    return quadkey

def tms2latlon(xtile,ytile,zoom):
    n = 2**zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

def latlon2tms(lat,lon,zoom):
    """
    Converts lat/lon (in degrees) to tile x/y coordinates in the given zoomlevel.
    Note that it doesn't give integers! If you need integers, truncate
    the result yourself.
    """
    n = 2**zoom
    lat_rad = math.radians(lat)
    xtile = (lon+ 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return (xtile, ytile)
