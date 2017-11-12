# -*- coding: utf-8 -*-
"""
Created on Fri Apr 14 13:45:02 2017

@author: Kyle
"""

import math

def find_pixel_centroid(x,y):
    """ 
    Summary:
    Returns the lat-long centroid of a given x-y pixel coordinates
    
    Input Arguments:    
    x,y: An x-y pixel pair of a given coordinate
    
    Output:
    The estimated lat-long centroid of a given x-y pixel
    """
    # See formulas from find_pixel_coords for more info
    x1 = 75.6-x/108.907 
    x2 = 75.6-(x+1)/108.907
    y1 = y/138.2 + 38
    y2 = (y+1)/138.2 + 38 
    return -(x1+x2)/2,(y1+y2)/2
    

def find_pixel_coords(lat, lon):
    """ 
    Summary:
    Returns the pixel coordinates of a given lat-lon on a uniform pixel
    grid centered in New Jersey
    
    Input Arguments:    
    lat, lon: A lat-long pair to convert to a pixel
    
    Output:
    The X and Y Coordinates of the pixel to which this lat-long belongs
    """
    lat, lon = float(lat), float(lon)
    xCoord = math.floor(108.907*(lon+75.6))
    yCoord = math.floor(138.2*(lat-38.9))
    return xCoord, yCoord