from math import pi, sin, cos, atan2, hypot

from ModestMaps.Geo import MercatorProjection
from ModestMaps.Core import Point

def deg2rad(deg):
    return pi * float(deg) / 180

def rad2deg(rad):
    return 180 * float(rad) / pi

def build_rough_placement_polygon(aspect, ul_lat, ul_lon, lr_lat, lr_lon):
    ''' Return rough placement geometry.
    
        Length of map hypotenuse in mercator units, angle of hypotenuse
        in radians counter-clockwise from due east, and footprint polygon.
    '''
    merc = MercatorProjection(0)
    
    #
    # Get the natural angle of the hypotenuse from map aspect ratio,
    # measured from the lower-right to the upper-left corner and expressed
    # in CCW radians from due east.
    #
    base_theta = atan2(1, -float(aspect))

    #
    # Convert corner lat, lons to conformal mercator projection
    #
    ul = merc.rawProject(Point(deg2rad(ul_lon), deg2rad(ul_lat)))
    lr = merc.rawProject(Point(deg2rad(lr_lon), deg2rad(lr_lat)))
    
    #
    # Derive dimensions of map in mercator units.
    #
    map_hypotenuse = hypot(ul.x - lr.x, ul.y - lr.y)
    map_width = map_hypotenuse * sin(base_theta - pi/2)
    map_height = map_hypotenuse * cos(base_theta - pi/2)
    
    #
    # Get the placed angle of the hypotenuse from the two placed corners,
    # again measured from the lower-right to the upper-left corner and
    # expressed in CCW radians from due east.
    #
    place_theta = atan2(ul.y - lr.y, ul.x - lr.x)
    diff_theta = place_theta - base_theta
    
    #
    # Derive the other two corners of the roughly-placed map,
    # and make a polygon in mercator units.
    #
    dx = map_height * sin(diff_theta)
    dy = map_height * cos(diff_theta)
    ur = Point(lr.x - dx, lr.y + dy)
    
    dx = map_width * cos(diff_theta)
    dy = map_width * sin(diff_theta)
    ll = Point(lr.x - dx, lr.y - dy)
    
    poly = [(ul.x, ul.y), (ur.x, ur.y), (lr.x, lr.y), (ll.x, ll.y)]
    
    return map_hypotenuse, diff_theta, poly
