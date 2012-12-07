var errorMsgs = {
    'filetype' : "Only 'csv' & 'txt' file extensions accepted.",
    'url': "That's not a valid URL."
}

window.onload = function(){
    var fileSelector = document.getElementById('csv-file-selector'); 
    if(fileSelector){
        var submitBtn = (document.getElementById('csv-submit-btn')) ? document.getElementById('csv-submit-btn').getElementsByTagName('button')[0] : null; 
        if(submitBtn){
            // do something
        }
        
        // form validation
        var form = document.getElementById('upload-form');
        if(form){
            form.onsubmit = function(evt){
                var elm,helps;
                var valid = true;    
                
                
                for(var i=0;i<this.elements.length;i++){
                    elm = this.elements[i];
                    if(elm.type != "submit"){
                        helps = elm.parentNode.getElementsByClassName('required'); 
                        if(!elm.value.length){ 
                            valid = false;
                            
                            for(var t=0;t<helps.length;t++){
                                if(!helps[t].classList.contains('valid-url'))helps[t].classList.remove('hide');
                             }
                             
                             if(elm.name == "url"){ 
                                 elm.parentNode.getElementsByClassName('valid-url')[0].classList.add('hide');
                             }
                             
                        }else{
                            for(var t=0;t<helps.length;t++){
                                if(!helps[t].classList.contains('valid-url'))helps[t].classList.add('hide');
                             } 
                             
                             if(elm.name == "url"){ 
                                 
                                 // 
                                 var help = elm.parentNode.getElementsByClassName('valid-url')[0];
                                 if(!validateURL(elm.value)){ 
                                     valid = false;
                                     help.innerHTML = errorMsgs['url'];
                                     help.classList.remove('hide');
                                     
                                 }else if(!validateFileType(elm.value)){ 
                                     valid = false;  
                                     help.innerHTML = errorMsgs['filetype'];
                                     help.classList.remove('hide');
                                    
                                 }else{
                                     help.classList.add('hide');
                                 }
                             }
                        }
                    }
                }

                return valid; 
                
            }
        }
        
    }
    
    
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

String.prototype.trim = String.prototype.trim || function trim() { return this.replace(/^\s\s*/, '').replace(/\s\s*$/, ''); };

function validateFileType(url){
    var accepted = ['csv','txt']; 
    url = url.split("?")[0]; 
    
    var extension = url.split('.').pop();  
    return (accepted.indexOf(extension.trim()) != -1) ? true : false;
}

function validateURL(url) {
    return /^(https?|ftp):\/\/(((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:)*@)?(((\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5])\.(\d|[1-9]\d|1\d\d|2[0-4]\d|25[0-5]))|((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?)(:\d*)?)(\/((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)+(\/(([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)*)*)?)?(\?((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|[\uE000-\uF8FF]|\/|\?)*)?(\#((([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(%[\da-f]{2})|[!\$&'\(\)\*\+,;=]|:|@)|\/|\?)*)?$/i.test(url);
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

