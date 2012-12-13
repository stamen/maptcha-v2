import logging
from StringIO import StringIO
from tempfile import mkdtemp
from math import pi, hypot, log, ceil
from os.path import join, splitext, basename, dirname
from xml.etree.ElementTree import Element, ElementTree
from multiprocessing import Process, JoinableQueue
from subprocess import Popen, PIPE
from urllib import urlencode, unquote_plus
from shutil import rmtree

from geometry import deg2rad, rad2deg, build_rough_placement_polygon

from ModestMaps.Geo import MercatorProjection, Transformation, deriveTransformation
from ModestMaps.Core import Point, Coordinate

from PIL import Image 
from shapely.geometry import Polygon

# Transformation from pi-based Mercator to earth radius
terra = Transformation(6378137, 0, 0, 0, 6378137, 0)

def preview_url(ul, ur, lr, ll):
    '''
    '''
    merc = MercatorProjection(0)
    
    ul = merc.rawUnproject(Point(*ul))
    ur = merc.rawUnproject(Point(*ur))
    lr = merc.rawUnproject(Point(*lr))
    ll = merc.rawUnproject(Point(*ll))
    
    q = dict(width='512', height='384', module='map')

    ulx, uly, urx, ury, lrx, lry, llx, lly \
        = [rad2deg(v) for v in (ul.x, ul.y, ur.x, ur.y, lr.x, lr.y, ll.x, ll.y)]

    xmin, ymin = min(ulx, urx, lrx, llx), min(uly, ury, lry, lly)
    xmax, ymax = max(uly, ury, lry, lly), max(ulx, urx, lrx, llx)
    perimeter = (ulx, uly, urx, ury, lrx, lry, llx, lly, ulx, uly)

    q.update(dict(polygons=','.join(['%.4f' % v for v in perimeter])))
    q.update(dict(bbox=','.join(('%.4f' % xmin, '%.4f' % ymax, '%.4f' % xmax, '%.4f' % ymin))))
    
    return 'http://pafciu17.dev.openstreetmap.org/?' + urlencode(q)

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

def coord2bbox(coord):
    '''
    '''
    radius = pi * 6378137
    
    xmin = coord.column / float(2**coord.zoom) - 0.5
    ymax = 0.5 - coord.row / float(2**coord.zoom)

    xmax = xmin + 1.0 / 2**coord.zoom
    ymin = ymax - 1.0 / 2**coord.zoom
    
    xmin, ymin, xmax, ymax = [2 * radius * v for v in (xmin, ymin, xmax, ymax)]
    
    return xmin, ymin, xmax, ymax

def native_zoom(w, h, ul, lr):
    '''
    '''
    # pixel size of spherical mercator tile at z=12
    m12_px_size = hypot(2*pi*6378137, 2*pi*6378137) / hypot(2**20, 2**20)

    # pixel size of image
    img_px_size = hypot(ul.x - lr.x, ul.y - lr.y) / hypot(w, h)
    
    # best native zoom level of image
    return 12 + log(m12_px_size / img_px_size) / log(2)

def cut_map_tiles(src_name, queue, ul, ur, lr, ll, max_zoom):
    '''
    '''
    coords = [Coordinate(0, 0, 0)]
    radius = pi * 6378137
    
    map_bounds = Polygon([(ul.x, ul.y), (ur.x, ur.y), (lr.x, lr.y), (ll.x, ll.y), (ul.x, ul.y)])
    
    while coords:
        coord = coords.pop(0)
        xmin, ymin, xmax, ymax = coord2bbox(coord)
        tile_bounds = Polygon([(xmin, ymax), (xmax, ymax), (xmax, ymin), (xmin, ymin), (xmin, ymax)])
        
        if tile_bounds.disjoint(map_bounds):
            continue
        
        tilename = join(dirname(src_name), 'tile-%(zoom)d-%(column)d-%(row)d.tif' % coord.__dict__)

        cmd = 'gdalwarp -r cubicspline -dstalpha -ts 256 256'.split()
        cmd += ('-te %(xmin).6f %(ymin).6f %(xmax).6f %(ymax).6f' % locals()).split()
        cmd += ['-overwrite', src_name, tilename] 
        cmd = Popen(cmd, stdout=PIPE, stderr=PIPE)
        cmd.wait()
        
        if cmd.returncode != 0:
            print cmd.stderr.read()
            raise Exception('Error in gdalwarp')
        
        queue.put((coord, tilename))
        
        if coord.zoom < max_zoom:
            coords.append(coord.zoomBy(1))
            coords.append(coord.zoomBy(1).right())
            coords.append(coord.zoomBy(1).right().down())
            coords.append(coord.zoomBy(1).down())

def upload_map_tiles(queue, bucket, dirname):
    '''
    '''
    while True:
        try:
            coord, tilename = queue.get(timeout=10)
        except:
            break
        
        buffer = StringIO()
        tile = Image.open(tilename)
        tile.save(buffer, 'PNG')
        
        key = '%s/%d/%d/%d.png' \
            % (dirname, coord.zoom, coord.column, coord.row)

        try:
            key = bucket.new_key(key)
            key.set_contents_from_string(buffer.getvalue(), {'Content-Type': 'image/png'}, policy='public-read')

        except:
            queue.put((coord, tilename))
            logging.error(repr(key))
        
        else:
            logging.info(repr(key))

def generate_map_tiles(atlas_dom, map_dom, bucket, map_id):
    '''
    '''
    map = map_dom.get_item(map_id, consistent_read=True)
    
    for key in ('version', 'aspect', 'ul_lat', 'ul_lon', 'lr_lat', 'lr_lon'):
        if key not in map:
            # we need these six keys to do anything meaningful
            logging.error('Map %s missing key "%s"' % (map.name, key))
            return
    
    #
    # Retrieve the original uploaded image from storage.
    #
    
    img = bucket.get_key(map['image'])
    if not img:
        # started using unqoute_plus to name the keys, to handle double encoding of file names on S3
        img = bucket.get_key(unquote_plus(map['image']))
    
    # ok give up
    if not img:
        logging.error("No image found for map: %s"%(map.name))
        return 
    
    
    tmpdir = mkdtemp(prefix='gen-map-tiles-')
    imgname = join(tmpdir, basename(img.name))
    
    img.get_contents_to_filename(imgname)
    img = Image.open(imgname)
    w, h = img.size
    
    #
    # Calculate a geo transformation based on three corner points.
    #
    size, theta, (ul, ur, lr, ll) \
        = build_rough_placement_polygon(map['aspect'], map['ul_lat'], map['ul_lon'], map['lr_lat'], map['lr_lon'])
    
    logging.info(preview_url(ul, ur, lr, ll))
    
    ul = terra.transform(Point(*ul))
    ur = terra.transform(Point(*ur))
    ll = terra.transform(Point(*ll))
    lr = terra.transform(Point(*lr))
    
    args = (0, 0, ul.x, ul.y, 0, h, ll.x, ll.y, w, h, lr.x, lr.y)
    xform = deriveTransformation(*args)
    
    #
    # Build a VRT file in spherical mercator projection.
    #
    vrtname = join(tmpdir, 'image.vrt')
    vrt = build_vrt(basename(imgname), img.size[0], img.size[1], xform)
    vrt.write(open(vrtname, 'w'))
    
    key = bucket.new_key(join(dirname(map['image']), 'image.vrt'))
    key.set_contents_from_filename(vrtname, {'Content-Type': 'application/gdal-vrt+xml'}, policy='public-read')
    
    #
    # Generate image tiles and upload them.
    #
    queue = JoinableQueue()
    tiles = join(dirname(map['image']), 'tiles-v%(version)s' % map)

    uploader1 = Process(target=upload_map_tiles, args=(queue, bucket, tiles))
    uploader2 = Process(target=upload_map_tiles, args=(queue, bucket, tiles))
    
    uploader1.start()
    uploader2.start()
    
    max_zoom = round(1 + native_zoom(w, h, ul, lr))
    logging.info("max_zoom from native_zoom: %s"%(max_zoom))
    # cap zoom at 18
    max_zoom = min(max_zoom,18.0)
    cut_map_tiles(vrtname, queue, ul, ur, lr, ll, max_zoom)
    
    uploader1.join()
    uploader2.join()
    
    #
    # Clean up.
    #
    rmtree(tmpdir)
    
    logging.info('Set %s on %s' % (repr(dict(tiles=basename(tiles))), map.name))
    
    map_dom.put_attributes(map.name, dict(tiles=basename(tiles)), expected_value=['version', map['version']])
