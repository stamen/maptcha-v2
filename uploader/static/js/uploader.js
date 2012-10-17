window.onload = function(){
    var fileSelector = document.getElementById('csv-file-selector');
    var submitBtn = document.getElementById('csv-submit-btn').getElementsByTagName('button')[0];
    var jumpers =  document.getElementsByClassName('top-jumper');
    var aniId = null;
    
    
    fileSelector.onchange = function(){ 
        if(this.value){
            submitBtn.disabled = false;
            submitBtn.classList.remove('disabled');
        }else{
            submitBtn.disabled = true;
            submitBtn.classList.add('disabled');
        } 
    }
    
    for(var i=0;i<jumpers.length;i++){
        jumpers[i].onclick = function(){ 
            if(aniId)stopScrollPage();
            scrollPage(window.scrollY);
            
            return false;
        }
    } 
    
    function stopScrollPage(){
        window.cancelAnimationFrame(aniId);
        aniId = null;
    }
    
    function scrollPage(y){ 
        if(y<1){
            stopScrollPage();
            return;
        }
        aniId = window.requestAnimationFrame(function(){     
            y -= 80; 
            if(y<0)y=0;
            window.scrollTo(0,y);
            scrollPage(y); 
        });

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

