(function(exports){
    
    if(typeof YTOB === "undefined")YTOB = {};
    YTOB.PlaceMap = {}; 
    
    var xform,canvas,image,arm,circle,pin,handle,imageHint,handleHint,canvasBg;  
    
    var armLength = 250,
        baseScale = 1,
        padding = 15;
    
    var downHandle = null,
        downMatrix = null,
        activeDrag = null,
        lastClick = false; 
        
    var oldmap = {
            opacity: 0.4,
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
    var geocoder = null;
    var ul_lat,ul_lon,lr_lat,lr_lon;
   
    var options = {
        'zoom-out-class':'zoom-out',
        'zoom-in-class':'zoom-in',
        'slider':{
            'id':'slide',
            'output':'slider-output-value',
            'overlay':'slide-overlay'
        },
        'background-map-id':'background-map',
        'background-map':{
            'id':'background-map',
            'provider':'terrain-background',
            'provider-alt':'terrain',
            'provider-alt-zoom-switch':12
        },
        'placement-map':{
            'map-id':'map-pane',
            'controls-id':'zoom-controls-mm'
        },
        'old-map':{
            'canvas-id':'scan',
            'ref-image-id':'scan_img'
        }
    }
    
    var windowSize = {
        w:null,
        h:null
    }
    
    var backgroundMap = null,
        backgroundMapLayer = null, 
        backgroundMapProviderBasic = null,
        backgroundMapProviderComplete = null;



    var displayHints = false;
    var lastRot = 0;     
    
    function setCanvasObjects(){ 
        var hintStyles = { fillColor: 'black', fontSize: '16', font: 'Helvetica, Arial, sans-serif' };
        $("#zoom-controls-canvas").find('.zoom-in').on('click',function(e){
            e.preventDefault();
            zoomInAbout(paper.view.center); 
        });
        $("#zoom-controls-canvas").find('.zoom-out').on('click',function(e){
            e.preventDefault();
            zoomOutAbout(paper.view.center); 
        });
        
        canvasBg.fillColor = '#ccc';
        canvasBg.strokeColor = "#ccc";
        canvasBg.strokeWidth = 1;   
        canvasBg.opacity = 1;
        
        pin.fillColor = '#F8F801';
        pin.strokeColor = '#F8F801';
        pin.strokeWidth = 1;

        handle.fillColor = '#F8F801';
        
        if(displayHints){
            imageHint.content = '(Drag to move)';
            imageHint.characterStyle = hintStyles;

            handleHint.content = '(Rotate & scale)';
            handleHint.characterStyle = hintStyles; 
        }
        
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
         
        

        var lenAB = Math.sqrt(Math.pow((pin.position.x - handle.position.x),2) + Math.pow((pin.position.y - handle.position.y),2));

        var newLength = 40;
        var newEndPt = new paper.Point(0,0);
        newEndPt.x = handle.position.x + (handle.position.x - pin.position.x) / lenAB * newLength;
        newEndPt.y = handle.position.y + (handle.position.y - pin.position.y) / lenAB * newLength;    
        //var angle =  Math.atan2((newEndPt.y - pin.position.y), (newEndPt.x - pin.position.x)) * (180/Math.PI); 

        arm = new paper.Path.Line(newEndPt, pin.position) 
        
        var rot = xform.getRotation();

        handle.rotate( rot - lastRot )
        lastRot = rot; 

        
        rotator.insertChild(0, arm);

        arm.strokeColor = '#F8F801'; // yellow
        arm.strokeWidth = 5;
        arm.opacity = 1;
        arm.dashArray = [14, 6];

        var s = handle.position.rotate(1, pin.position),
            c = handle.position.rotate(180, pin.position),
            e = handle.position.rotate(-1, pin.position);

        circle = new paper.Path.Arc(s, c, e); 

        rotator.insertChild(0, circle);

        circle.strokeColor = '#F8F801';
        circle.strokeWidth = 8;
        circle.opacity = 1;
        circle.dashArray = [14, 7];

        if(displayHints)handleHint.position = addPoints(handle.position , new paper.Point(-170, 5)); 
    }
    
    function clampArm(x,y){ 
        var w = Math.sqrt(Math.pow((pin.position.x - x),2) + Math.pow((pin.position.y - y),2));
        if(w > mapSize.w/2){
            var angle =  Math.atan2((y - pin.position.y), (x - pin.position.x)) ;
            x = paper.view.center.x + r * Math.cos(angle);
            y = paper.view.center.y + r * Math.sin(angle);
        }
        
        return [x,y]
    }
    
    function onMouseDown(event)
    {
        if(event.point.isInside(handle.bounds)) {
            downHandle = handle.position.clone();
            downMatrix = xform.clone();
            activeDrag = handle;
            if(displayHints)handleHint.visible = false; 
            

        } else {
            activeDrag = image;
            if(displayHints)imageHint.visible = false;
            canvas.style.cursor = 'move';
        }
    }  
    
    function subtractPoints(pt1,pt2){ 
          return new paper.Point(pt1.x - pt2.x, pt1.y - pt2.y);
    } 
    function addPoints(pt1,pt2){
          return new paper.Point(pt1.x + pt2.x, pt1.y + pt2.y);
    }
    
    var lastAngle,prevPos;
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
            var pt = clampArm(x,y);
            x = pt[0];
            y = pt[1];
            
           
            canvas.style.cursor = 'pointer';

            handle.position = new paper.Point(x, y);

            updateArmAndCircle();
            
            var currentVector = subtractPoints(handle.position,pin.position),
            lastVector = subtractPoints(downHandle, pin.position),
            angle = currentVector.angle - lastVector.angle,
            scale = currentVector.length / lastVector.length;

            //handle.rotate( angle)
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
        
        
        var oldVec = handle.position.clone();
        var scale = vec.length / oldVec.length;  
        
        
        
        //handle.position = subtractPoints(handle.position,vec);
        
        //handle.position = addPoints(paper.view.center , new paper.Point(armLength * Math.cos(-Math.PI/3), armLength * Math.sin(-Math.PI/3))); 
        updateArmAndCircle();

        xform.preConcatenate(paper.Matrix.getTranslateInstance(-point.x, -point.y));
        xform.preConcatenate(paper.Matrix.getScaleInstance(.7071, .7071));
        xform.preConcatenate(paper.Matrix.getTranslateInstance(point.x, point.y));

        image.setMatrix(xform);
        paper.view.draw(); 
        updateImagePosition();
    }

    function zoomInAbout(point)
    {  
        var vec = subtractPoints(handle.position, pin.position);
        var zoomFactor = (1.4142 - 1);  
        vec.x *= zoomFactor; 
        vec.y *= zoomFactor;
        
        
        
        //handle.position = addPoints(handle.position , vec);
        
        //handle.position = addPoints(paper.view.center , new paper.Point(armLength * Math.cos(-Math.PI/3), armLength * Math.sin(-Math.PI/3)));

        updateArmAndCircle();

        xform.preConcatenate(paper.Matrix.getTranslateInstance(-point.x, -point.y));
        xform.preConcatenate(paper.Matrix.getScaleInstance(1.4142, 1.4142));
        xform.preConcatenate(paper.Matrix.getTranslateInstance(point.x, point.y));

        image.setMatrix(xform);  
        
        paper.view.draw();
        updateImagePosition();
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
    
    
    var minimumWidth = 980;
    var boxContainer = null;
    
    function getContainerSizes(){
        windowSize.w = window.innerWidth,
        windowSize.h = window.innerHeight; 
        
        var box = boxContainer.width();
        
        //windowSize.w = Math.min(windowSize.w,maximumWidth)  
        var inner = windowSize.w;
        if(inner < minimumWidth)inner = minimumWidth;
        inner *= .9;

        
        mapSize.w = Math.floor(box/2) - 1;
        mapSize.h = Math.floor(windowSize.h - 90);
        
        //console.log(windowSize.w + " :: " + mapSize.w + " :: "+box/2)
    }   
    
    
    
    /* PUBLIC */
    YTOB.PlaceMap.updatePaperViewSize = function(w,h){ 
        if(!paper)return; 
        
        paper.view.viewSize = new paper.Size(w,h); 
        
        paper.view.draw();
    } 
    
    YTOB.PlaceMap.resize = function(){ 
        
        getContainerSizes(); 
        
        if(backgroundMap){
            backgroundMap.setSize(new MM.Point(windowSize.w,windowSize.h))
        }
        
        var cx = (mapSize.w/2) - paper.view.center._x;
        var cy = (mapSize.h/2) - paper.view.center._y;
        var pt = new paper.Point(cx,cy);
        
        $("#scan-box").css("height",mapSize.h+"px");
        innerMapOffset = $("#map-box").offset(); 
        
        if(map){
            map.setSize(new MM.Point(mapSize.w,mapSize.h));
            updateBackgroundMap(); 
            updateOldMap();  
        }
           
        if(image){
            YTOB.PlaceMap.updatePaperViewSize(mapSize.w,mapSize.h);

            canvasBg.setBounds(paper.view.bounds);
            xform.translate(pt);
            image.setMatrix(xform);   
        
            pin.position = paper.view.center;
        
            handle.position.x += pt.x;
        
            updateArmAndCircle();
            updateImagePosition();
              
            paper.view.draw();
        }
        
       
        return; 

        var cx = (mapSize.w/2) - paper.view.center._x;
        var cy = (mapSize.h/2) - paper.view.center._y;
        var pt = new paper.Point(cx,cy); 
        
        var lft = (windowSize.w - (mapSize.w * 2)) / 2;  
        
        //pt.x *= xform.scaleX;
        //pt.y *= xform.scaleY;
        
       //$(".box").css("width",mapSize.w+"px");  
       $("#scan-box").css("height",mapSize.h+"px");   
       
        if(image){
            YTOB.PlaceMap.updatePaperViewSize(mapSize.w,mapSize.h);

            canvasBg.setBounds(paper.view.bounds);
            xform.translate(pt);
            image.setMatrix(xform);   
        
            pin.position = paper.view.center;
        
            handle.position.x += pt.x;
        
            updateArmAndCircle();
            updateImagePosition();
              
            paper.view.draw();
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
        canvas = document.getElementById(options['old-map']['canvas-id']);
        paper.setup(canvas);   
        
        YTOB.PlaceMap.updatePaperViewSize(mapSize.w,mapSize.h);
        
        xform = paper.Matrix.getTranslateInstance(paper.view.center);
        xform.scale(baseScale);
         
        canvasBg = new paper.Path.Rectangle(paper.view.bounds);  
        
        image = new paper.Raster(options['old-map']['ref-image-id']); 
        image.setMatrix(xform); 

        pin = new paper.Path.Oval(new paper.Rectangle(paper.view.center.x - 13, paper.view.center.y - 13, 26, 26));  
        
        var handleBk = new paper.Path.Rectangle(paper.view.center.x - 13, paper.view.center.y - 13, 26, 26) 
        
        // little markers in the handle
        var lineSize = 7;
        var mark1 = new paper.Path();
        var mark2 = new paper.Path();
        
        mark1.strokeColor = "black";
        mark1.strokeWidth = 2;
        mark1.fillColor = "black";
        mark2.strokeColor = "black";
        mark2.strokeWidth = 2;
        mark2.fillColor = "black";
        
        mark1.add( new paper.Point(paper.view.center.x ,paper.view.center.y - lineSize) );
        mark1.add( new paper.Point(paper.view.center.x + lineSize,paper.view.center.y - lineSize) );
        mark1.add( new paper.Point(paper.view.center.x + lineSize,paper.view.center.y ) );
        mark2.add( new paper.Point(paper.view.center.x - lineSize ,paper.view.center.y) );
        mark2.add( new paper.Point(paper.view.center.x - lineSize ,paper.view.center.y + lineSize) );
        mark2.add( new paper.Point(paper.view.center.x ,paper.view.center.y + lineSize) );
        
        handle = new paper.Group([handleBk,mark1,mark2]);
        
        var rotatorGroup = [pin, handle];
        
        if(displayHints){
            imageHint = new paper.PointText(new paper.Point(60, 25));
            handleHint = new paper.PointText(paper.view.center); 
            rotatorGroup.push(handleHint);
        }
        
        
        rotator = new paper.Group(rotatorGroup);
        rotator.visible = false;
        
        handle.rotate(45 - handle.position.angle);
        
        setCanvasObjects();
        
        
        var tool = new paper.Tool();
        tool.onMouseDown = onMouseDown; 
        tool.onMouseMove = onMouseMove;
        tool.onMouseUp = onMouseUp;
        
        updateImagePosition(); 
        
        updateArmAndCircle();
        
        paper.view.draw();

    } 


    YTOB.PlaceMap.initBackgroundMap = function(){
        backgroundMapLayer = new MM.StamenTileLayer(options['background-map']['provider']);   
        
        backgroundMapProviderBasic = backgroundMapLayer.provider; 
        
        if(options['background-map']['provider-alt']){
            backgroundMapProviderComplete = new MM.StamenTileLayer(options['background-map']['provider-alt']).provider;
        } 
        
        var size = new MM.Point(windowSize.w,windowSize.h);
        backgroundMap = new MM.Map(options['background-map']['id'], backgroundMapLayer,size,[new MM.DragHandler(map)]); 

        backgroundMap.setCenterZoom(new MM.Location(37.7, -122.4), 12); 
    }
    
    
    YTOB.PlaceMap.initMap = function(){
        var layer = new MM.StamenTileLayer("terrain-background"); 
        
        map = new MM.Map(options['placement-map']['map-id'], layer); 

        map.setSize(new MM.Point(mapSize.w,mapSize.h));
    
        if(atlas_hints.ul_lat && atlas_hints.ul_lon && atlas_hints.lr_lat && atlas_hints.lr_lon){
            var ext = new MM.Extent( new MM.Location(atlas_hints.ul_lat,atlas_hints.lr_lon), new MM.Location(atlas_hints.lr_lat,atlas_hints.ul_lon) );
            map.setExtent(ext);
        }else{
            map.setCenterZoom(new MM.Location(37.7, -122.4), 12); 
        }
        
        exports.ymap = map;   

        $(layer.parent).css("opacity",0);
        
        $("#"+options['placement-map']['controls-id']).find('.' + options['zoom-in-class']).on('click',function(e){
            e.preventDefault();
            map.zoomIn();
        });
        $("#"+options['placement-map']['controls-id']).find('.' + options['zoom-out-class']).on('click',function(e){
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
            slider = $("#"+options['slider']['id']);
            slider.attr("value",oldmap.opacity * 100);  
            
            var sliderOutput = $("#"+options['slider']['output']);
            var sliderOverlay = $("#"+options['slider']['overlay']);
          
             
            slider.on('change',function(e){
                this.value = this.value; // wierd
                
                sliderOutput.text(this.value + "%"); 
                sliderOverlay.css("width",(this.value + "%"));
                changeOverlay( this.value / 100);
            });
              
            slider.on("mousedown",function(){
                oldmap.untouched = false;
            }); 
            slider.trigger("change");
        }
         
        mainMapZoomed();
        updateOldMap();
        YTOB.PlaceMap.showRotator();  

        return map;
    }

    function updateArmAndCircleFromKeyBoard(matrixClone,prevHandlePos){
        var currentVector = subtractPoints(handle.position,pin.position),
        lastVector = subtractPoints(prevHandlePos, pin.position),
        angle = currentVector.angle - lastVector.angle,
        scale = currentVector.length / lastVector.length;   
        YTOB.ole = matrixClone;
        
        //handle.rotate( angle)
        if(scale > 0)
        {
            xform = matrixClone;
            xform.preConcatenate(paper.Matrix.getTranslateInstance(-paper.view.center.x, -paper.view.center.y));
            xform.preConcatenate(paper.Matrix.getRotateInstance(angle));
            xform.preConcatenate(paper.Matrix.getScaleInstance(scale, scale));
            xform.preConcatenate(paper.Matrix.getTranslateInstance(paper.view.center.x, paper.view.center.y));
            
            image.setMatrix(xform);
        }
    } 
    function scaleArmAndCircleIn(){
        var lenAB = Math.sqrt(Math.pow((pin.position.x - handle.position.x),2) + Math.pow((pin.position.y - handle.position.y),2)); 
        var newLength = .9;
        var pos = new paper.Point(0,0);
        var x = handle.position.x + (handle.position.x - pin.position.x) / lenAB * newLength;
        var y = handle.position.y + (handle.position.y - pin.position.y) / lenAB * newLength; 
        var pt = clampArm(x,y);
        
        pos.x = pt[0];
        pos.y = pt[1];
        
        
        return pos;
    }
    function scaleArmAndCircleOut(){
        var lenAB = Math.sqrt(Math.pow((pin.position.x - handle.position.x),2) + Math.pow((pin.position.y - handle.position.y),2)); 
        var newLength = .9;
        var pos = new paper.Point(0,0);
        var x = handle.position.x - (handle.position.x - pin.position.x) / lenAB * newLength;
        var y = handle.position.y - (handle.position.y - pin.position.y) / lenAB * newLength;
        var pt = clampArm(x,y);
        
        pos.x = pt[0];
        pos.y = pt[1]; 
        
        return pos;
    }
    
    function newPointForArmFromKeyboard(dir){
        dir = dir || 1;
        var w = Math.sqrt(Math.pow((pin.position.x - handle.position.x),2) + Math.pow((pin.position.y - handle.position.y),2));
        var angle =  Math.atan2((handle.position.y - pin.position.y), (handle.position.x - pin.position.x));
       
        if(dir < 1){
            angle += .005;
        }else{
            angle -= .005;
        }

        var x = paper.view.center.x + w * Math.cos(angle);
        var y = paper.view.center.y + w * Math.sin(angle);
        
        return new paper.Point(x,y);
    }
    
    
    function setKeyboardShortCuts(){
        $(window).on('keydown',function(e){

           if(!e.keyCode)return;
           
           switch(e.keyCode){
                case 37: // left (rotate left)
                    var preMatrix = xform.clone();
                    var oldHandlePos =  handle.position.clone();

                    handle.position = newPointForArmFromKeyboard(1);
                    
                    updateArmAndCircle(); 
                    updateArmAndCircleFromKeyBoard(preMatrix,oldHandlePos); 
 
                    paper.view.draw();
                    updateImagePosition();  
                break; 
                case 39: // right (rotate right)
                    var preMatrix = xform.clone();
                    var oldHandlePos =  handle.position.clone();
                    
                    handle.position = newPointForArmFromKeyboard(-1);
                    updateArmAndCircle(); 
                    updateArmAndCircleFromKeyBoard(preMatrix,oldHandlePos); 
 
                    paper.view.draw();
                    updateImagePosition(); 
                break;
                case 38: // up (scale up)
                    var preMatrix = xform.clone();
                    var oldHandlePos =  handle.position.clone();
                    
                    handle.position = scaleArmAndCircleIn();
                    updateArmAndCircle(); 
                    updateArmAndCircleFromKeyBoard(preMatrix,oldHandlePos); 
 
                    paper.view.draw();
                    updateImagePosition();
                

                break;
                case 40: // down (scale dwn)
                    var preMatrix = xform.clone();
                    var oldHandlePos =  handle.position.clone();

                    handle.position = scaleArmAndCircleOut();
                    updateArmAndCircle(); 
                    updateArmAndCircleFromKeyBoard(preMatrix,oldHandlePos); 
 
                    paper.view.draw();
                    updateImagePosition();
                break;
                
                
           }
        });
    }
    
    YTOB.PlaceMap.init = function(){  
        boxContainer = $("#positioners-container");
        
        // get some initial sizes...
        getContainerSizes(); 
        
        YTOB.PlaceMap.initBackgroundMap();
        YTOB.PlaceMap.initCanvas();
        YTOB.PlaceMap.initMap();
        
        geocoder = new YTOB.Geocoder();
        setKeyboardShortCuts(); 
        
    } 
    
    function changeOverlay(value)
    {
        oldmap.opacity = value;
        updateOldMap();
        return false;
    } 
    
    function mainMapZoomed(){    

        if(!backgroundMap)return; 
        
        if(backgroundMapProviderComplete){
            if(map.getZoom() >= options['background-map']['provider-alt-zoom-switch']){   
                backgroundMapLayer.setProvider(backgroundMapProviderComplete);   
            }else{
                backgroundMapLayer.setProvider(backgroundMapProviderBasic); 
            }
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

        
        var ul = matrix.transform({x: 0, y: 0}),
            ur = matrix.transform({x: image.width, y: 0}),
            lr = matrix.transform({x: image.width, y: image.height}),
            ll = matrix.transform({x: 0, y: image.height});


        var latlon = function(p) { return map.pointLocation(p) },
            point = function(l) { return l.lon.toFixed(8) + ' ' + l.lat.toFixed(8) };
        
        /*
        var origin = latlon(ul),
            center = latlon(matrix.transform({x: image.width/2, y: image.height/2})),
            footprint = [latlon(ul), latlon(ur), latlon(lr), latlon(ll), latlon(ul)];
        */
        
        var corners = {
            'ul':latlon(ul),
            'lr':latlon(lr)
        };
        
        if(!ul_lat)ul_lat = $("#ul_lat");
        if(!ul_lon)ul_lon = $("#ul_lon");
        if(!lr_lat)lr_lat = $("#lr_lat");
        if(!lr_lon)lr_lon = $("#lr_lon"); 
        
        ul_lat.attr("value",corners.ul.lat);
        ul_lon.attr("value",corners.ul.lon);
        lr_lat.attr("value",corners.lr.lat);
        lr_lon.attr("value",corners.lr.lon);

    }
    
    function updateImageGeography(image, matrix, scale)
    {
        oldmap.image = image;
        oldmap.matrix = matrix;

        updateOldMap();
    }
    

    /// GEOCODER 
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

            if(atlas_hints.lr_lat && atlas_hints.ul_lon && atlas_hints.ul_lat && atlas_hints.lr_lon){
                this.southwest = new google.maps.LatLng(atlas_hints.lr_lat,atlas_hints.ul_lon);
                this.northeast = new google.maps.LatLng(atlas_hints.ul_lat,atlas_hints.lr_lon); 
            }else{
                this.southwest = new google.maps.LatLng(37.7077, -122.5169);
                this.northeast = new google.maps.LatLng(37.8153, -122.3559);
            } 

            if(atlas_hints.has_streets){
                $('#explain-title').html(hint_attr['streets']['explain-title']);
                $('#explain-help').html(hint_attr['streets']['explain-help']);  
                $('#address_input').attr("placeholder",hint_attr['streets']['placeholder']);
            }else if(atlas_hints.has_cities){
                $('#explain-title').html(hint_attr['cities']['explain-title']);
                $('#explain-help').html(hint_attr['cities']['explain-help']);  
                $('#address_input').attr("placeholder",hint_attr['cities']['placeholder']);
            }else if(atlas_hints.has_features){
                $('#explain-title').html(hint_attr['features']['explain-title']);
                $('#explain-help').html(hint_attr['features']['explain-help']);  
                $('#address_input').attr("placeholder",hint_attr['features']['placeholder']);
            }else{
                $('#explain-title').html(hint_attr['default']['explain-title']);
                $('#explain-help').html(hint_attr['default']['explain-help']);  
                $('#address_input').attr("placeholder",hint_attr['default']['placeholder']);
            }
            
            this.bounds = new google.maps.LatLngBounds(this.southwest, this.northeast); 
            this.input = $("#address_input");
            
            this.input.on("change",function(e){
                e.preventDefault(); 
                
                self.jumpAddress(this.value);
            }); 

            $("#address_input_submit").on('click',function(e){
                e.preventDefault();  
                self.jumpAddress(self.input.val());
            });  
            
            $("#address-search-form .close").on('click',function(e){
                e.preventDefault();
                $("#address-search").removeClass("no-map");
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
    
    //http://unscriptable.com/2009/03/20/debouncing-javascript-methods/
    var debounce = function (func, threshold, execAsap) {

        var timeout;

        return function debounced () {
            var obj = this, args = arguments;
            function delayed () {
                if (!execAsap)
                    func.apply(obj, args);
                timeout = null; 
            };

            if (timeout)
                clearTimeout(timeout);
            else if (execAsap)
                func.apply(obj, args);

            timeout = setTimeout(delayed, threshold || 100); 
        };

    }
    
    exports.YTOB.debounce = debounce; 
  

})(this)