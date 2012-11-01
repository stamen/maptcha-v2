import logging
from tempfile import mkdtemp
from os.path import join, splitext, basename
from xml.etree.ElementTree import Element, ElementTree
from urllib import urlencode
from shutil import rmtree

from geometry import deg2rad, rad2deg, build_rough_placement_polygon

from ModestMaps.Geo import MercatorProjection, Transformation, deriveTransformation
from ModestMaps.Core import Point

from PIL import Image 

# Transformation from pi-based Mercator to earth radius
T = Transformation(6378137, 0, 0, 0, 6378137, 0)

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

def build_vrt(name, width, height, xform):
    '''
        <VRTDataset rasterXSize="1536" rasterYSize="1266">
          <GeoTransform>-13662019.9611, 36.730660425, 0.490168756898, 4579531.35076, 0.490168756824, -36.7306604305</GeoTransform>
          <SRS>PROJCS[&quot;unnamed&quot;,GEOGCS[&quot;unnamed ellipse&quot;,DATUM[&quot;unknown&quot;,SPHEROID[&quot;unnamed&quot;,6378137,0],EXTENSION[&quot;PROJ4_GRIDS&quot;,&quot;@null&quot;]],PRIMEM[&quot;Greenwich&quot;,0],UNIT[&quot;degree&quot;,0.0174532925199433]],PROJECTION[&quot;Mercator_2SP&quot;],PARAMETER[&quot;standard_parallel_1&quot;,0],PARAMETER[&quot;central_meridian&quot;,0],PARAMETER[&quot;false_easting&quot;,0],PARAMETER[&quot;false_northing&quot;,0],UNIT[&quot;Meter&quot;,1]]</SRS>
          <Metadata />
          <VRTRasterBand dataType="Byte" band="1">
            <Metadata />
            <ColorInterp>Red</ColorInterp>
            <SimpleSource>
              <SourceFilename relativeToVRT="1">image.jpg</SourceFilename>
              <SourceBand>1</SourceBand>
              <SourceProperties RasterXSize="1536" RasterYSize="1266" DataType="Byte" BlockXSize="1536" BlockYSize="1" />
              <SrcRect xOff="0" yOff="0" xSize="1536" ySize="1266" />
              <DstRect xOff="0" yOff="0" xSize="1536" ySize="1266" />
            </SimpleSource>
          </VRTRasterBand>
          <VRTRasterBand dataType="Byte" band="2">
            <Metadata />
            <ColorInterp>Green</ColorInterp>
            ...
          </VRTRasterBand>
          <VRTRasterBand dataType="Byte" band="3">
            <Metadata />
            <ColorInterp>Blue</ColorInterp>
            ...
          </VRTRasterBand>
        </VRTDataset>
    '''
    vrt = Element('VRTDataset', rasterXSize=str(width), rasterYSize=str(height))
    
    geo = Element('GeoTransform')
    geo.text = ', '.join(['%.9f' % getattr(xform, a) for a in 'cx ax bx cy ay by'.split()])
    vrt.append(geo)
    
    srs = Element('SRS')
    srs.text = 'PROJCS["unnamed",GEOGCS["unnamed ellipse",DATUM["unknown",SPHEROID["unnamed",6378137,0],EXTENSION["PROJ4_GRIDS","@null"]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Mercator_2SP"],PARAMETER["standard_parallel_1",0],PARAMETER["central_meridian",0],PARAMETER["false_easting",0],PARAMETER["false_northing",0],UNIT["Meter",1]]'
    vrt.append(srs)
    
    for (num, chan) in [('1', 'Red'), ('2', 'Green'), ('3', 'Blue')]:
        
        raster = Element('VRTRasterBand', dataType='Byte', band=num)
        
        color = Element('ColorInterp')
        color.text = chan
        
        source = Element('SimpleSource')
        
        fname = Element('SourceFilename', relativeToVRT='1')
        fname.text = name
        
        sband = Element('SourceBand')
        sband.text = num
        
        props = Element('SourceProperties', RasterXSize=str(width), RasterYSize=str(height),
                        DataType='Byte', BlockXSize=str(width), BlockYSize='1')
        
        srect = Element('SrcRect', xOff='0', yOff='0', xSize=str(width), ySize=str(height))
        drect = Element('DstRect', xOff='0', yOff='0', xSize=str(width), ySize=str(height))

        source.append(fname)
        source.append(sband)
        source.append(props)
        source.append(srect)
        source.append(drect)
        
        raster.append(color)
        raster.append(source)
        
        vrt.append(raster)
    
    return ElementTree(vrt)

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
    
    vrt = build_vrt(basename(filename), img.size[0], img.size[1], xform)
    vrt.write(open(join(dirname, 'image.vrt'), 'w'))
    
    raise Exception()
    
    rmtree(dirname)
