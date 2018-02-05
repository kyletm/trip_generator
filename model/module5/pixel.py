# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 13:45:02 2017

@author: Kyle
"""

import math

def find_pixel_centroid(x, y):
    """Returns the lat-lon corner of a given x-y pixel coordinates
    
    Inputs:    
        x,y (int): An x-y pixel pair of a given coordinate
    
    Returns:
        lat, lon (float): lat, lon corner of a given x-y pixel coordinate
    """
    # See formulas from find_pixel_coords for more info
    lat = y/138.348 + 37.0
    lon = x/(138.348*math.cos(math.pi/180 * lat)) - 97.5
    return lat, lon
    

def find_pixel_coords(lat, lon):
    """Returns pixel coordinates on a uniform grid centered on U.S.
    
    Inputs:    
        lat, lon (float): A lat-long pair to convert to a pixel
    
    Returns:
        xCoord, yCoord (int): x, y pixel coordinates
    """
    lat, lon = float(lat), float(lon)
    xCoord = math.floor(138.348*(lon+97.5)*math.cos(lat*math.pi/180))
    yCoord = math.floor(138.348*(lat-37.0))
    return xCoord, yCoord