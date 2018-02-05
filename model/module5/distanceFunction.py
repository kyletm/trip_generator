# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 22:32:51 2016

@author: Kyle
"""
import math
'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS '
def distance_between_counties(lat1, lon1, lat2, lon2):
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    try:
        arc = math.acos(cos)
    except:
        arc = 0.000001
    return arc * 3963.167