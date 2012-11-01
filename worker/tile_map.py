import logging
from tempfile import mkdtemp
from os.path import join, splitext
from urllib import urlencode
from shutil import rmtree

from geometry import deg2rad, rad2deg, build_rough_placement_polygon

from ModestMaps.Geo import MercatorProjection, Transformation, deriveTransformation
from ModestMaps.Core import Point

from PIL import Image 

R = 6378137 # earth radius
T = Transformation(R, 0, 0, 0, R, 0)
merc = MercatorProjection(0, T)

def showme(ul, ur, lr, ll):
    '''
    '''
    merc = MercatorProjection(0)
    
    ul = merc.rawUnproject(Point(*ul))
    ur = merc.rawUnproject(Point(*ur))
    lr = merc.rawUnproject(Point(*lr))
    ll = merc.rawUnproject(Point(*ll))
    
    q = dict(width='512', height='384', module='map')

    ulx, uly, urx, ury, lrx, lry, llx, lly = [rad2deg(v) for v in (ul.x, ul.y, ur.x, ur.y, lr.x, lr.y, ll.x, ll.y)]

    q.update(dict(polygons=','.join(['%.6f' % v for v in (ulx, uly, urx, ury, lrx, lry, llx, lly, ulx, uly)])))
    q.update(dict(bbox=','.join(('%.6f' % min(ulx, urx, lrx, llx), '%.6f' % max(uly, ury, lry, lly), '%.6f' % max(ulx, urx, lrx, llx), '%.6f' % min(uly, ury, lry, lly)))))
    
    print 'http://pafciu17.dev.openstreetmap.org/?' + urlencode(q)

def generate_map_tiles(atlas_dom, map_dom, bucket, map_id):
    '''
    '''
    map = map_dom.get_item(map_id, consistent_read=True)
    
    for key in ('version', 'aspect', 'ul_lat', 'ul_lon', 'lr_lat', 'lr_lon'):
        if key not in map:
            # we need these six keys to do anything meaningful
            logging.error('Map %s missing key "%s"' % (map.name, key))
            return
    
    print map['version']
    print map['ul_lat'], map['ul_lon'], map['lr_lat'], map['lr_lon']
    
    size, theta, (ul, ur, lr, ll) \
        = build_rough_placement_polygon(map['aspect'], map['ul_lat'], map['ul_lon'], map['lr_lat'], map['lr_lon'])
    
    showme(ul, ur, lr, ll)
    

    
    ul = T.transform(Point(*ul))
    ll = T.transform(Point(*ll))
    lr = T.transform(Point(*lr))
    
    print 'Corners:', ul, ll, lr
    
    
    
    img = bucket.get_key(map['image'])
    dirname = mkdtemp(prefix='gen-map-tiles-')
    filename = join(dirname, 'image' + splitext(img.name)[1])
    
    print filename
    
    img.get_contents_to_filename(filename)
    img = Image.open(filename)
    w, h = img.size
    print w, h
    
    from math import hypot
    print hypot(lr.x - ll.x, lr.y - ll.y) / w,
    print hypot(ll.x - ul.x, ll.y - ul.y) / h
    
    args = (0, 0, ul.x, ul.y, 0, h, ll.x, ll.y, w, h, lr.x, lr.y)
    xform = deriveTransformation(*args)
    
    print xform.ax, xform.bx, xform.cx, xform.ay, xform.by, xform.cy
    
    raise Exception()
    
    rmtree(dirname)
