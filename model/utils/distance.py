'''
Module for distance related functionality. 
'''
import math

# equitorial radius of the earth, in miles
RADIUS = 3963.167

def to_cart(lat, lon):
    """Converts lat, lon coordinates to cartesian coordinates.

    See: https://rbrundritt.wordpress.com/2008/10/14/
    conversion-between-spherical-and-cartesian-coordinates-systems/
    for derviation.
    
    Inputs:
        lat, lon (float): Coordinate pair.
    
    Returns:
        x, y, z (float): Cartesian transformation.
    """
    degrees_to_radians = math.pi/180.0
    lat_rad = lat * degrees_to_radians
    lon_rad = lon * degrees_to_radians
    x = RADIUS * math.cos(lat_rad) * math.cos(lon_rad)
    y = RADIUS * math.cos(lat_rad) * math.sin(lon_rad)
    z = RADIUS * math.sin(lat_rad)
    return x, y, z

def between_points(lat1, lon1, lat2, lon2):
    """Computes great circle distance between two lat-lon pairs.

    Inputs:
        lat1, lon1 (float): First coordinate pair.
        lat2, lon2 (float): Second coordinate pair.
    
    Returns:
        dist (float): Great circle distance between two points.
    """
    degrees_to_radians = math.pi/180.0
    phi1 = (90.0 - float(lat1))*degrees_to_radians
    phi2 = (90.0 - float(lat2))*degrees_to_radians
    theta1 = float(lon1)*degrees_to_radians
    theta2 = float(lon2)*degrees_to_radians
    cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
           math.cos(phi1)*math.cos(phi2))
    arc = math.acos(cos)
    return arc * RADIUS
    
def between_pixels(x1, y1, x2, y2):
    """Computes great circle distance between two lat-lon pairs.

    Inputs:
        lat1, lon1 (float): First coordinate pair.
        lat2, lon2 (float): Second coordinate pair.
    
    Returns:
        dist (float): Great circle distance between two points.
    """
    if x1 == x2 and y1 == y2:
        # Area of a pixel
        dist = 0.25
    else:
        dist = math.sqrt((x2-x1)**2 + (y2-y1)**2)
    return dist