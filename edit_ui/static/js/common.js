function timeConverter(UNIX_timestamp){ 
    UNIX_timestamp = parseInt(UNIX_timestamp)*1000;
    var ts = new Date(UNIX_timestamp);
    var yr = ts.getUTCFullYear();
    var month = ts.getUTCMonth();
    var day = ts.getUTCDate();
    var hour = ts.getUTCHours();
    var min = ts.getUTCMinutes();
    var sec = ts.getUTCSeconds(); 
    var milli = ts.getUTCMilliseconds();
    var new_date = new Date(yr,month,day,hour,min,sec,milli);

    return new_date;
}

function getElementsByClass(searchClass,node,tag) {
	var classElements = new Array();
	if ( node == null )
		node = document;
	if ( tag == null )
		tag = '*';
	var els = node.getElementsByTagName(tag);
	var elsLen = els.length;
	var pattern = new RegExp("(^|\\s)"+searchClass+"(\\s|$)");
	for (i = 0, j = 0; i < elsLen; i++) {
		if ( pattern.test(els[i].className) ) {
			classElements[j] = els[i];
			j++;
		}
	}
	return classElements;
} 

//
var poller = {
    queue:[], // {id:ID to check, dom:related dom element to update} 
    run: function(){  
        if (!this.queue.length)return; 
        var url = "/check-map-status/"+this.queue[this.queue.length-1].id 
        this.xhr(url);
    },
    resp: function(r){ 
       if(r && r.response){
          var json = JSON.parse(r.response);
          if(json['status'] == 'error'){
              this.queue.pop();
              return;
          }
          
          if (json['status'] == "finished"){ 
              var dom = this.queue[this.queue.length-1].dom;
              dom.classList.remove('empty');
              dom.classList.add('finished');
              this.queue.pop();
              
          }
         
         this.run(); 
         //this.run(q)
       }
      
    },
    //#https://github.com/d3/d3.github.com/blob/master/d3.v2.js
    xhr: function(url) {
        var self = this;
        var mime = 'application/json';
        var req = new XMLHttpRequest;
        if (arguments.length < 3) callback = mime, mime = null; else if (mime && req.overrideMimeType) req.overrideMimeType(mime);
        req.open("GET", url, true);
        if (mime) req.setRequestHeader("Accept", mime);
        req.onreadystatechange = function() {
            if (req.readyState === 4) {
                var s = req.status;
                var rsp = (!s && req.response || s >= 200 && s < 300 || s === 304) ? req : null;
                self.resp(rsp);
            }
        };
        req.send(null);
    } 
}