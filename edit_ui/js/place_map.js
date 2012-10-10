(function(exports){
    

    if(typeof YTOB === "undefined")YTOB = {};
    YTOB.PlaceMap = {};

    YTOB.PlaceMap.initCanvas = function(){ 
        var armLength = 250,
            baseScale = 1,
            padding = 10; 
            
            
        paper.setup('scan');
        
        
        var xform = Matrix.getTranslateInstance(view.center);
        xform.scale(baseScale);  
    
        var bg = new Path.Rectangle(view.bounds);
        var img = new Raster('scan_img'); 
    
        bg.fillColor = 'red';
        
        img.position = view.center; 
        //img.scale(1)
        //img.transform(xform);
        
        view.draw();
    }
    YTOB.PlaceMap.initMap = function(selector){
        var layer = new MM.StamenTileLayer("toner-lite");
        var map = new MM.Map(selector, layer);
        map.setCenterZoom(new MM.Location(37.7, -122.4), 12); 
        
        
        
        
        return map;
    }
    exports.YTOB = YTOB;   
    
    
})(this)