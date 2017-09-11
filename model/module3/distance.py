'''
distance.py

author: Matthew Garvey
purpose: module for determining the disance between two points
'''
import math

'RETURN MILES BETWEEN LATITUDE AND LONGITUDE POINTS'
def CurvedDistance_between_LonLatPoints(lat1, lon1, lat2, lon2):
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    return arc * 3963.167


'RETURN LINEAR APPROXIMATION OF DISTANCE BETWEEN POINTS'
def LinearDistance_between_PixelatedPoints(x1, y1, x2, y2):
	return math.sqrt((x1-x2)**2 + (y1-y2)**2)
	


