(function(exports){
    

    if(typeof YTOB === "undefined")YTOB = {};
    YTOB.PlaceMap = {}; 
    
    var xform,canvas,image,arm,circle,pin,handle,imageHint,handleHint,canvasBg;  
    
    var armLength = 250,
        baseScale = 1,
        padding = 10;
    
    var downHandle = null,
        downMatrix = null,
        activeDrag = null,
        lastClick = false; 
        
    var oldmap = {
            opacity: 0,
            untouched: true,
            image: null,
            matrix: null
          },
        map = null,
        mapCanvas = null,
        slider = null;
        
        
    var mapSize = {
        w:480,
        h:550
    }
                      
    
    function setCanvasObjects(){ 
        
        $("#zoom-controls-canvas").find('.zoom-in').on('click',function(e){
            e.preventDefault();
            zoomInAbout(paper.view.center); 
        });
        $("#zoom-controls-canvas").find('.zoom-out').on('click',function(e){
            e.preventDefault();
            zoomOutAbout(paper.view.center); 
        });
        
        canvasBg.fillColor = null;
        canvasBg.strokeColor = "black";
        canvasBg.strokeWidth = 1; 
        
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
        if(event.delta.length < 3) {
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
    
    var windowSize = {
        w:null,
        h:null
    }
    
    function getContainerSizes(){
        windowSize.w = window.innerWidth,
        windowSize.h = window.innerHeight;
        
        mapSize.w = Math.floor(windowSize.w * .40);
        mapSize.h = Math.floor(windowSize.h - 90);
    }   
    
    
    /* PUBLIC */
    YTOB.PlaceMap.updatePaperViewSize = function(w,h){ 
        if(!paper)return; 
        
        paper.view.viewSize = new paper.Size(w,h); 
        
        
        paper.view.draw();
    } 
    
    YTOB.PlaceMap.resize = function(){
        getContainerSizes(); 
        
        
        
        var cx = (mapSize.w/2) - paper.view.center._x;
        var cy = (mapSize.h/2) - paper.view.center._y;
        var pt = new paper.Point(cx,cy); 
        
        var lft = (windowSize.w - (mapSize.w * 2)) /2;  
        /*
        $("#scan-box").css({
            'margin-left':lft + "px"
        })*/
        
        //pt.x *= xform.scaleX;
        //pt.y *= xform.scaleY;
        
       $(".box").css("width",mapSize.w+"px");  
       $("#scan-box").css("height",mapSize.h+"px");
        if(image){
            YTOB.PlaceMap.updatePaperViewSize(mapSize.w,mapSize.h);    
        
            xform.translate(pt);
            image.setMatrix(xform);   
        
            pin.position = paper.view.center;
        
            handle.position.x += pt.x;
        
            updateArmAndCircle();
            updateImagePosition(); 
        }
        
        innerMapOffset = $("#map-box").offset();
        
        if(backgroundMap){
            backgroundMap.setSize(new MM.Point(windowSize.w,windowSize.h))
        }
 
        if(map){
            map.setSize(new MM.Point(mapSize.w,mapSize.h));
            updateBackgroundMap(); 
            updateOldMap();  
        }
        
    }
    
    
    YTOB.PlaceMap.showRotator = function()
    {
        rotator.visible = true;
        paper.view.draw();
    }
    
    YTOB.PlaceMap.initCanvas = function(){ 
        canvas = document.getElementById('scan');
        paper.setup(canvas);   
        
        YTOB.PlaceMap.updatePaperViewSize(mapSize.w,mapSize.h);
        
        xform = paper.Matrix.getTranslateInstance(paper.view.center);
        xform.scale(baseScale);
         
        canvasBg = new paper.Path.Rectangle(paper.view.bounds);
        
        image = new paper.Raster('scan_img'); 
        image.setMatrix(xform); 

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
    
    
    
    var backgroundMap = null,
        backgroundMapLayer = null, 
        backgroundMapProviderBasic = null,
        backgroundMapProviderComplete = null;  
        
    YTOB.PlaceMap.initBackgroundMap = function(selector){
        backgroundMapLayer = new MM.StamenTileLayer("terrain-background");   
        
        backgroundMapProviderBasic = backgroundMapLayer.provider;  
        backgroundMapProviderComplete = new MM.StamenTileLayer("terrain").provider;
        
        backgroundMap = new MM.Map(selector, backgroundMapLayer); 

        backgroundMap.setSize(new MM.Point(windowSize.w,windowSize.h));
        backgroundMap.setCenterZoom(new MM.Location(37.7, -122.4), 12); 
        
        
    }
    
    YTOB.PlaceMap.initMap = function(selector){
        var layer = new MM.StamenTileLayer("terrain-background"); 
        
        
        map = new MM.Map(selector, layer); 

        map.setSize(new MM.Point(mapSize.w,mapSize.h));
        map.setCenterZoom(new MM.Location(37.7, -122.4), 12);   

        $(layer.parent).css("opacity",0);
        
        $("#zoom-controls-mm").find('.zoom-in').on('click',function(e){
            e.preventDefault();
            map.zoomIn();
        });
        $("#zoom-controls-mm").find('.zoom-out').on('click',function(e){
            e.preventDefault();
            map.zoomOut();
        });   
        
        
        map.addCallback('panned', function(m,offset) { 
            if(backgroundMap){
               backgroundMap.panBy(offset[0], offset[1]); 
            }
        
        });    
        
        map.addCallback("zoomed", mainMapZoomed);
        map.addCallback("extentset", updateBackgroundMap);
        map.addCallback("centered", updateBackgroundMap);

        
         
        mapCanvas = document.createElement('canvas');
        mapCanvas.width = backgroundMap.dimensions.x;
        mapCanvas.height = backgroundMap.dimensions.y;
        backgroundMap.parent.appendChild(mapCanvas);  
        
        if(!slider){
            slider = $("#slide");
            slider.attr("value",oldmap.opacity * 100); 
            var sliderOutput = slider.parent().find("span");
            
            slider.on("change",function(e){ 
                this.value = this.value; // wierd  
                sliderOutput.text(this.value + "%");
                changeOverlay(this.value/100);
            });
            slider.on("mousedown",function(){
                oldmap.untouched = false;
            });
            sliderOutput.text(slider.attr('value') + "%");
        }
         
        mainMapZoomed();
        updateOldMap();
        YTOB.PlaceMap.showRotator();  

        return map;
    }
    
    
    
    
    YTOB.PlaceMap.init = function(selector){ 
        getContainerSizes();
        YTOB.PlaceMap.initBackgroundMap('background-map');
        YTOB.PlaceMap.initCanvas();
        YTOB.PlaceMap.initMap(selector);  
     
    } 
    
    function changeOverlay(value)
    {
        oldmap.opacity = value;
        updateOldMap();
        return false;
    } 
    
    function mainMapZoomed(){    

        if(!backgroundMap)return;
        if(map.getZoom() >= 12){   
            backgroundMapLayer.setProvider(backgroundMapProviderComplete);   
        }else{
            backgroundMapLayer.setProvider(backgroundMapProviderBasic); 
        } 
        
        updateBackgroundMap();
    }
    
    var innerMapOffset = null;
    function updateBackgroundMap(){
        if(!backgroundMap)return; 
        if(!innerMapOffset)innerMapOffset = $("#map-box").offset(); 
        
        var oft = innerMapOffset,
            centerPt = map.locationPoint(map.getCenter());        
            
        backgroundMap.setCenterZoom(backgroundMap.pointLocation(centerPt),map.getZoom());  
        
        var backgroundMapCenterPt = backgroundMap.locationPoint(map.getCenter());  
            
        var ofx = (oft.left + mapSize.w/2) - windowSize.w/2 ; 
        var ofy = (oft.top + mapSize.h/2) - windowSize.h/2; 
                
        backgroundMapCenterPt.x -= ofx; 
        backgroundMapCenterPt.y -= ofy; 
        
        backgroundMap.setCenterZoom(backgroundMap.pointLocation(backgroundMapCenterPt),map.getZoom());   
        var dest = mapCanvas.getContext('2d');
        
        
    }
    
    function updateOldMap()
    {
        if(!mapCanvas)
        {
            return;
        } 
        
        if(!innerMapOffset)innerMapOffset = $("#map-box").offset();
        
        var dest = mapCanvas.getContext('2d'),
            matrix = oldmap.matrix,
            image = oldmap.image;
        
        mapCanvas.width = windowSize.w;
        mapCanvas.height = windowSize.h;
        dest.clearRect(0, 0, windowSize.w, windowSize.h);

        dest.save();
        
        dest.translate(innerMapOffset.left,20);
        dest.transform(matrix._a, matrix._c, matrix._b, matrix._d, matrix._tx, matrix._ty);
        
        dest.globalAlpha = oldmap.opacity;
        dest.drawImage(image, 0, 0);

        dest.restore();


        dest.beginPath();
        dest.lineWidth = 1;
        dest.fillStyle = '#f1e6c8';
        dest.strokeStyle = 'black';
                             

        var centerX = mapCanvas.width/2 + mapSize.w/2,
            centerY = mapCanvas.height/2;
        dest.moveTo(centerX  + 4, centerY);

        for(var t = Math.PI/16; t <= Math.PI*2; t += Math.PI/16)
        {
            dest.lineTo(centerX + 4 * Math.cos(t), centerY + 4 * Math.sin(t));
        }

        dest.closePath();
        dest.fill();
        dest.stroke();
      
        
        var ul = matrix.transform({x: 0, y: 0}),
            ur = matrix.transform({x: image.width, y: 0}),
            lr = matrix.transform({x: image.width, y: image.height}),
            ll = matrix.transform({x: 0, y: image.height});
 
        dest.beginPath();
        dest.lineWidth = 0;
        dest.strokeStyle = 'rgba(0, 0, 0, 0)';

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

        //document.getElementById('origin-wkt').value = 'POINT('+point(origin)+')';
        //document.getElementById('center-wkt').value = 'POINT('+point(center)+')';
        //document.getElementById('footprint-wkt').value = 'POLYGON(('+footprint.map(point).join(',')+'))';
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
            this.geocoder.geocode({address: address, bounds: this.bounds}, this.onGeocoded);
            return false;
        }
    } 
  
    
    
    
    exports.YTOB = YTOB;
})(this)