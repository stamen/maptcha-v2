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

//TODO: not thoughly tested for browser support, will not work for IE < 8
var poller = { 
    rate: 5000,
    queueHash:{},
    atlas_id:'',
    checkClass:'empty',
    callback:null,
    run: function(){  
        var url = "/check-map-status/"+this.atlas_id;
        this.xhr(url);
    },
    check:function(){ 
        if(!this.atlas_id)return;
        
        var empties = getElementsByClass(this.checkClass); 
        if(empties && empties.length){
            this.queueHash = {};
            for(var i=0;i<empties.length;i++){
                var id = empties[i].getAttribute('id');
                this.queueHash[id] = empties[i];
            }
            this.update(empties.length); 
            
            var self = this;
            window.setTimeout(function(){self.run();},this.rate); 
            
        }else{
            this.update(0)
        }
        
    },
    update: function(t){ 
       if(this.callback){
           this.callback(t);
       }
    },
    setCallback:function(f){
        f = f || null;
        this.callback = (f.constructor && f.call && f.apply) ? f : null;
    },
    resp: function(r){ 
        if(r && r.response){
            var json = JSON.parse(r.response); 
                        
            if(json['error']){  
                // do an error handler here 
            }

            if (json['uploaded']){ 
                var ids = json['uploaded'];
                for(var i=0;i<ids.length;i++){ 
                    var id = 'thumb-'+ids[i];
                    if(this.queueHash[id]){
                        var elm = this.queueHash[id];
                        if(elm){
                            var img = elm.getElementsByTagName('img');
                            if(img){
                                img = img[0];
                                img.setAttribute('src',img.getAttribute('src'));

                            } 
                            elm.classList.remove('empty');
                            elm.classList.add('uploaded');
                        }
                    }
                }
            } 
        }   
        this.check();
      
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

/*
 * classList.js: Cross-browser full element.classList implementation.
 * 2011-06-15
 *
 * By Eli Grey, http://eligrey.com
 * Public Domain.
 * NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.
 */
 
/*global self, document, DOMException */
 
/*! @source http://purl.eligrey.com/github/classList.js/blob/master/classList.js*/
 
if (typeof document !== "undefined" && !("classList" in document.createElement("a"))) {
 
(function (view) {
 
"use strict";
 
var
      classListProp = "classList"
    , protoProp = "prototype"
    , elemCtrProto = (view.HTMLElement || view.Element)[protoProp]
    , objCtr = Object
    , strTrim = String[protoProp].trim || function () {
        return this.replace(/^\s+|\s+$/g, "");
    }
    , arrIndexOf = Array[protoProp].indexOf || function (item) {
        var
              i = 0
            , len = this.length
        ;
        for (; i < len; i++) {
            if (i in this && this[i] === item) {
                return i;
            }
        }
        return -1;
    }
    // Vendors: please allow content code to instantiate DOMExceptions
    , DOMEx = function (type, message) {
        this.name = type;
        this.code = DOMException[type];
        this.message = message;
    }
    , checkTokenAndGetIndex = function (classList, token) {
        if (token === "") {
            throw new DOMEx(
                  "SYNTAX_ERR"
                , "An invalid or illegal string was specified"
            );
        }
        if (/\s/.test(token)) {
            throw new DOMEx(
                  "INVALID_CHARACTER_ERR"
                , "String contains an invalid character"
            );
        }
        return arrIndexOf.call(classList, token);
    }
    , ClassList = function (elem) {
        var
              trimmedClasses = strTrim.call(elem.className)
            , classes = trimmedClasses ? trimmedClasses.split(/\s+/) : []
            , i = 0
            , len = classes.length
        ;
        for (; i < len; i++) {
            this.push(classes[i]);
        }
        this._updateClassName = function () {
            elem.className = this.toString();
        };
    }
    , classListProto = ClassList[protoProp] = []
    , classListGetter = function () {
        return new ClassList(this);
    }
;
// Most DOMException implementations don't allow calling DOMException's toString()
// on non-DOMExceptions. Error's toString() is sufficient here.
DOMEx[protoProp] = Error[protoProp];
classListProto.item = function (i) {
    return this[i] || null;
};
classListProto.contains = function (token) {
    token += "";
    return checkTokenAndGetIndex(this, token) !== -1;
};
classListProto.add = function (token) {
    token += "";
    if (checkTokenAndGetIndex(this, token) === -1) {
        this.push(token);
        this._updateClassName();
    }
};
classListProto.remove = function (token) {
    token += "";
    var index = checkTokenAndGetIndex(this, token);
    if (index !== -1) {
        this.splice(index, 1);
        this._updateClassName();
    }
};
classListProto.toggle = function (token) {
    token += "";
    if (checkTokenAndGetIndex(this, token) === -1) {
        this.add(token);
    } else {
        this.remove(token);
    }
};
classListProto.toString = function () {
    return this.join(" ");
};
 
if (objCtr.defineProperty) {
    var classListPropDesc = {
          get: classListGetter
        , enumerable: true
        , configurable: true
    };
    try {
        objCtr.defineProperty(elemCtrProto, classListProp, classListPropDesc);
    } catch (ex) { // IE 8 doesn't support enumerable:true
        if (ex.number === -0x7FF5EC54) {
            classListPropDesc.enumerable = false;
            objCtr.defineProperty(elemCtrProto, classListProp, classListPropDesc);
        }
    }
} else if (objCtr[protoProp].__defineGetter__) {
    elemCtrProto.__defineGetter__(classListProp, classListGetter);
}
 
}(self));
 
}