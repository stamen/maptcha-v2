(function(exports){
    

    if(typeof YTOB === "undefined")YTOB = {};
    YTOB.PlaceMap = {}; 
    
    var xform,canvas,image,zoomout,zoomin,arm,circle,pin,handle,imageHint,handleHint,canvasBg;
    var armLength = 250,
        baseScale = 1,
        padding = 10;
    
    var downHandle = null,
        downMatrix = null,
        activeDrag = null,
        lastClick = false; 
        
    var oldmap = {
            opacity: .05,
            untouched: true,
            image: null,
            matrix: null
          },
        map = null,
        mapCanvas = null,
        slider = null; 
                      
    
    function setCanvasObjects(){
        zoomout.position = new paper.Point(10 + zoomout.size.width/2, 10 + zoomout.size.height/2);
        zoomin.position = new paper.Point(10 + zoomout.size.width + zoomin.size.width/2, 10 + zoomin.size.height/2);

        pin.fillColor = '#f3f0ec';
        pin.strokeColor = 'black';
        pin.strokeWidth = 1;

        handle.fillColor = 'white';
        handle.strokeColor = 'black';
        handle.strokeWidth = 2;

        imageHint.content = '(Drag to move)';
        imageHint.characterStyle = { fillColor: 'black', fontSize: '16', font: 'Helvetica, Arial, sans-serif' };

        handleHint.content = '(Rotate & scale)';
        handleHint.characterStyle = { fillColor: 'black', fontSize: '16', font: 'Helvetica, Arial, sans-serif' };

        pin.position = paper.view.center;
        handle.position = addPoints(paper.view.center , new paper.Point(armLength * Math.cos(-Math.PI/3), armLength * Math.sin(-Math.PI/3)));
    } 
    
    
    function updateArmAndCircle()
    {
        if(arm) {
            arm.remove();
        }

        if(circle) {
            circle.remove();
        }

        arm = new paper.Path.Line(handle.position, pin.position);
        rotator.insertChild(0, arm);

        arm.strokeColor = 'black';
        arm.strokeWidth = 2;
        arm.opacity = 0.35;
        arm.dashArray = [3, 3];

        var s = handle.position.rotate(10, pin.position),
            c = handle.position.rotate(180, pin.position),
            e = handle.position.rotate(-10, pin.position);

        circle = new paper.Path.Arc(s, c, e);
        rotator.insertChild(0, circle);

        circle.strokeColor = 'black';
        circle.strokeWidth = 2;
        circle.opacity = 0.35;
        circle.dashArray = [3, 3];

        handleHint.position = addPoints(handle.position , new paper.Point(-170, 5));  
    }
    
    function onMouseDown(event)
    {
        if(event.point.isInside(handle.bounds)) {
            downHandle = handle.position.clone();
            downMatrix = xform.clone();
            activeDrag = handle;
            handleHint.visible = false; 
            

        } else if(event.point.isInside(zoomout.bounds)) {
            activeDrag = zoomout;

        } else if(event.point.isInside(zoomin.bounds)) {
            activeDrag = zoomin;

        } else {
            activeDrag = image;
            imageHint.visible = false;
            canvas.style.cursor = 'move';
        }
    }  
    
    function subtractPoints(pt1,pt2){
          return new paper.Point(pt1.x - pt2.x, pt1.y - pt2.y);
    } 
    function addPoints(pt1,pt2){
          return new paper.Point(pt1.x + pt2.x, pt1.y + pt2.y);
    }

    function onMouseMove(event)
    {
        var cursor = 'auto';
        
        
        cursor = event.point.isInside(handle.bounds) ? 'pointer' : cursor;
        cursor = event.point.isInside(zoomout.bounds) ? 'pointer' : cursor;
        cursor = event.point.isInside(zoomin.bounds) ? 'pointer' : cursor;
        canvas.style.cursor = cursor;

        if(!activeDrag) {
            return;
        }
         
        var x = Math.max(padding, Math.min(paper.view.bounds.right - padding, event.point.x)),
            y = Math.max(padding, Math.min(paper.view.bounds.bottom - padding, event.point.y));

        if(activeDrag == image) {
            canvas.style.cursor = 'move';

            xform.preConcatenate(paper.Matrix.getTranslateInstance(event.delta)); 
            
            image.setMatrix(xform)

        } else if(activeDrag == handle) {
            canvas.style.cursor = 'pointer';

            handle.position = new paper.Point(x, y);

            updateArmAndCircle();
            
            
            var currentVector = subtractPoints(handle.position,pin.position),
                lastVector = subtractPoints(downHandle, pin.position),
                angle = currentVector.angle - lastVector.angle,
                scale = currentVector.length / lastVector.length;
          
           
            if(scale > 0)
            {
                xform = downMatrix.clone();
                xform.preConcatenate(paper.Matrix.getTranslateInstance(-paper.view.center.x, -paper.view.center.y));
                xform.preConcatenate(paper.Matrix.getRotateInstance(angle));
                xform.preConcatenate(paper.Matrix.getScaleInstance(scale, scale));
                xform.preConcatenate(paper.Matrix.getTranslateInstance(paper.view.center.x, paper.view.center.y));
                
                image.setMatrix(xform);
            }
        }

        updateImagePosition();
    } 

    

    function zoomOutAbout(point)
    {   var vec = subtractPoints(handle.position, pin.position);
        if(vec.length < 2)
        {
            return;
        }

        var zoomFactor = (1 - .7071);  
        vec.x *= zoomFactor; 
        vec.y *= zoomFactor;   
        
        handle.position = subtractPoints(handle.position,vec); 
        updateArmAndCircle();

        xform.preConcatenate(paper.Matrix.getTranslateInstance(-point.x, -point.y));
        xform.preConcatenate(paper.Matrix.getScaleInstance(.7071, .7071));
        xform.preConcatenate(paper.Matrix.getTranslateInstance(point.x, point.y));

        image.setMatrix(xform);
    }

    function zoomInAbout(point)
    {  
        var vec = subtractPoints(handle.position, pin.position);
        var zoomFactor = (1.4142 - 1);  
        vec.x *= zoomFactor; 
        vec.y *= zoomFactor;
        
        handle.position = addPoints(handle.position , vec);

        updateArmAndCircle();

        xform.preConcatenate(paper.Matrix.getTranslateInstance(-point.x, -point.y));
        xform.preConcatenate(paper.Matrix.getScaleInstance(1.4142, 1.4142));
        xform.preConcatenate(paper.Matrix.getTranslateInstance(point.x, point.y));

        image.setMatrix(xform);
    }

    function onMouseUp(event)
    {
        if(activeDrag == zoomout) {
            zoomOutAbout(paper.view.center);

        } else if(activeDrag == zoomin) {
            zoomInAbout(paper.view.center);

        } else if(event.delta.length < 3) {
            var click = {point: event.point, time: (new Date()).getTime()};

            if(lastClick && (lastClick.time + 150) > click.time)
            {
                zoomInAbout(click.point);
            }

            lastClick = click;
        }

        activeDrag = null;
        canvas.style.cursor = 'auto';

        updateImagePosition();
    } 

    function updateImagePosition()
    {
        var _xform = xform.clone();
        _xform.translate(-image.width/2, -image.height/2);
        
        var vec = subtractPoints(handle.position , pin.position);
        var scale = vec.length / armLength;
        updateImageGeography(image.image, _xform, scale);
    } 
    
    
    /* PUBLIC */
    YTOB.PlaceMap.updatePaperViewSize = function(w,h){
        paper.view.viewSize = new paper.Size(w,h); 
        
    }
      
    YTOB.PlaceMap.showRotator = function()
    {
        rotator.visible = true;
        paper.view.draw();
    }
    
    YTOB.PlaceMap.initCanvas = function(){ 
        canvas = document.getElementById('scan');
        paper.setup(canvas);  
        
        //YTOB.PlaceMap.updatePaperViewSize(480,550);
        
        xform = paper.Matrix.getTranslateInstance(paper.view.center);
        xform.scale(baseScale);
         
        canvasBg = new paper.Path.Rectangle(paper.view.bounds);
        canvasBg.fillColor = 'silver';
        image = new paper.Raster('scan_img'); 
        image.setMatrix(xform); 
        
        zoomout = new paper.Raster('zoom-out-img');
        zoomin = new paper.Raster('zoom-in-img');
        pin = new paper.Path.Oval(new paper.Rectangle(paper.view.center.x - 4, paper.view.center.y - 4, 8, 8));
        handle = new paper.Path.Oval(new paper.Rectangle(paper.view.center.x - 8, paper.view.center.y - 8, 16, 16));
        imageHint = new paper.PointText(new paper.Point(10, 80));
        handleHint = new paper.PointText(paper.view.center); 
        
        rotator = new paper.Group([pin, handle, handleHint]);
        rotator.visible = false;


        setCanvasObjects();
        
        
        var tool = new paper.Tool();
        tool.onMouseDown = onMouseDown; 
        tool.onMouseMove = onMouseMove;
        tool.onMouseUp = onMouseUp;   
        
        updateImagePosition(); 
        
        updateArmAndCircle();
        
        paper.view.draw();  

    }
    
    YTOB.PlaceMap.initMap = function(selector){
        var layer = new MM.StamenTileLayer("toner-lite");
        map = new MM.Map(selector, layer);
        map.setCenterZoom(new MM.Location(37.7, -122.4), 12); 
        
        document.getElementById('zoom-out').style.display = 'inline';
        document.getElementById('zoom-in').style.display = 'inline'; 
        document.getElementById('zoom-out').onclick = function() { map.zoomOut(); return false; };
        document.getElementById('zoom-in').onclick = function() { map.zoomIn(); return false; };
         
        mapCanvas = document.createElement('canvas');
        mapCanvas.width = map.dimensions.x;
        mapCanvas.height = map.dimensions.y;
        map.parent.appendChild(mapCanvas);  
        
        if(!slider){
            slider = $("#slide");
            slider.attr("value",oldmap.opacity * 100);
            
            slider.on("change",function(e){  
                changeOverlay(this.value/100)
            });
            slider.on("mousedown",function(){
                oldmap.untouched = false;
            });
            
        }
        
        updateOldMap();
        YTOB.PlaceMap.showRotator();
        
        return map;
    } 
    
    function changeOverlay(value)
    {
        oldmap.opacity = value;
        updateOldMap();
        return false;
    }
    
    
    function updateOldMap()
    {
        if(!mapCanvas)
        {
            return;
        }
        
        var dest = mapCanvas.getContext('2d'),
            matrix = oldmap.matrix,
            image = oldmap.image;

        dest.clearRect(0, 0, 480, 550);

        dest.save();
        //dest.transform(matrix._m00, matrix._m10, matrix._m01, matrix._m11, matrix._m02, matrix._m12);
        dest.transform(matrix._a, matrix._c, matrix._b, matrix._d, matrix._tx, matrix._ty);
        dest.globalAlpha = oldmap.opacity;
        dest.drawImage(image, 0, 0);

        dest.restore();


        dest.beginPath();
        dest.lineWidth = 1;
        dest.fillStyle = '#f1e6c8';
        dest.strokeStyle = 'black';

        dest.moveTo(mapCanvas.width/2 + 4, mapCanvas.height/2);

        for(var t = Math.PI/16; t <= Math.PI*2; t += Math.PI/16)
        {
            dest.lineTo(mapCanvas.width/2 + 4 * Math.cos(t), mapCanvas.height/2 + 4 * Math.sin(t));
        }

        dest.closePath();
        dest.fill();
        dest.stroke();
      
        
        var ul = matrix.transform({x: 0, y: 0}),
            ur = matrix.transform({x: image.width, y: 0}),
            lr = matrix.transform({x: image.width, y: image.height}),
            ll = matrix.transform({x: 0, y: image.height});
 
        dest.beginPath();
        dest.lineWidth = 2;
        dest.strokeStyle = 'rgba(0, 0, 0, 0.35)';

        dest.moveTo(ul.x, ul.y);
        dest.lineTo(ur.x, ur.y);
        dest.lineTo(lr.x, lr.y);
        dest.lineTo(ll.x, ll.y);
        dest.lineTo(ul.x, ul.y);

        dest.closePath();
        dest.stroke();

        var latlon = function(p) { return map.pointLocation(p) },
            point = function(l) { return l.lon.toFixed(8) + ' ' + l.lat.toFixed(8) };

        var origin = latlon(ul),
            center = latlon(matrix.transform({x: image.width/2, y: image.height/2})),
            footprint = [latlon(ul), latlon(ur), latlon(lr), latlon(ll), latlon(ul)];

        document.getElementById('origin-wkt').value = 'POINT('+point(origin)+')';
        document.getElementById('center-wkt').value = 'POINT('+point(center)+')';
        document.getElementById('footprint-wkt').value = 'POLYGON(('+footprint.map(point).join(',')+'))';
    }
    
    function updateImageGeography(image, matrix, scale)
    {
        oldmap.image = image;
        oldmap.matrix = matrix;

        if(!slider)
        {
            return updateOldMap();
        }

        if(oldmap.untouched) {
            //var opacity = Math.max(0, Math.min((1/scale - 1) / 4)); 
            //slider.attr("value",opacity * 100)
            //changeOverlay(opacity);
            updateOldMap(); 
        } else {
            updateOldMap();
        }
    }  
    
      
    
    
    
    /// GEOCODER 
    var geocoder = null;
    YTOB.Geocoder = function(){  
        if(geocoder)return geocoder;
        
        
        this.init(); 
        geocoder = this;
    }
    
    YTOB.Geocoder.prototype = {
        geocoder: null,
        southwest: null,
        northeast: null,
        bounds: null,
        input:null,
        
        init: function(){ 
            var self = this; 
            
            this.geocoder = new google.maps.Geocoder();
            this.southwest = new google.maps.LatLng(37.7077, -122.5169);
            this.northeast = new google.maps.LatLng(37.8153, -122.3559);
            this.bounds = new google.maps.LatLngBounds(this.southwest, this.northeast); 
            this.input = $("#address-search").find('input');
            
            this.input.on("change",function(e){
                e.preventDefault();
                self.jumpAddress(this.value);
            });
        },
        onGeocoded: function(results, status){
            if(status != google.maps.GeocoderStatus.OK){
                alert('No such address.');
                return;
            }
            if(!map){
                
            }else{ 
                $("#address-search").removeClass('no-map');
                var viewport = results[0].geometry.viewport,
                    ne = viewport.getNorthEast(),
                    sw = viewport.getSouthWest(),
                    locations = [{lat: ne.lat(), lon: ne.lng()}, {lat: sw.lat(), lon: sw.lng()}];

                map.setExtent(locations);
                map.zoomBy(1);
            } 
            
        },
        jumpAddress: function(address){   
            console.log(this)
            this.geocoder.geocode({address: address, bounds: this.bounds}, this.onGeocoded);

            return false;
        }
    } 
  
    
    
    
    exports.YTOB = YTOB;
})(this)