window.onload = function(){
    var fileSelector = document.getElementById('csv-file-selector');
    var submitBtn = (document.getElementById('csv-submit-btn')) ? document.getElementById('csv-submit-btn').getElementsByTagName('button')[0] : null;
    var jumpers =  document.getElementsByClassName('top-jumper');
    var aniId = null; 
    var jumpStart = null;
    var jumpMove = 0;
    
    
     
    if(jumpers){   
         for(var i=0;i<jumpers.length;i++){
             jumpers[i].onclick = function(){ 
                 if(aniId)stopScrollPage();  
                 jumpStart = new Date();
                 jumpMove = window.scrollY;
                 scrollPage();
     
                 return false;
             }
         } 
    } 

    function stopScrollPage(){
        window.cancelAnimationFrame(aniId);
        aniId = null;
        jumpStart = null;
        jumpMove = 0;
    }

    function scrollPage(){ 
        var elapsed = new Date() - jumpStart;
        var progress = elapsed / 200;
        if (progress > 1) progress = 1;
        window.scrollTo(0,jumpMove - (jumpMove * progress)); 
        
        if (progress == 1){
            stopScrollPage(); 
            return;
        }
        
        aniId = window.requestAnimationFrame(scrollPage);
    }


} 

// Erik Möller requestAnimation polyfill
(function() {
    var lastTime = 0;
    var vendors = ['ms', 'moz', 'webkit', 'o'];
    for(var x = 0; x < vendors.length && !window.requestAnimationFrame; ++x) {
        window.requestAnimationFrame = window[vendors[x]+'RequestAnimationFrame'];
        window.cancelAnimationFrame = 
          window[vendors[x]+'CancelAnimationFrame'] || window[vendors[x]+'CancelRequestAnimationFrame'];
    }
 
    if (!window.requestAnimationFrame)
        window.requestAnimationFrame = function(callback, element) {
            var currTime = new Date().getTime();
            var timeToCall = Math.max(0, 16 - (currTime - lastTime));
            var id = window.setTimeout(function() { callback(currTime + timeToCall); }, 
              timeToCall);
            lastTime = currTime + timeToCall;
            return id;
        };
 
    if (!window.cancelAnimationFrame)
        window.cancelAnimationFrame = function(id) {
            clearTimeout(id);
        };
}());  

