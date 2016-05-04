{% autoescape None %}{% whitespace all %}
var docCookies = {
  getItem: function (sKey,escape) {
    if (!sKey) { return null; }
    var result = document.cookie.replace(new RegExp("(?:(?:^|.*;)\\s*" + encodeURIComponent(sKey).replace(/[\-\.\+\*]/g, "\\$&") + "\\s*\\=\\s*([^;]*).*$)|^.*$"), "$1") || null;
    if(result && escape !== false){
    	result = decodeURIComponent(result);
    }
    return result;
  },
  setItem: function (sKey, sValue, vEnd, sPath, sDomain, bSecure, escape) {
    if (!sKey || /^(?:expires|max\-age|path|domain|secure)$/i.test(sKey)) { return false; }
    var sExpires = "";
    if (vEnd) {
      switch (vEnd.constructor) {
        case Number:
          sExpires = vEnd === Infinity ? "; expires=Fri, 31 Dec 9999 23:59:59 GMT" : "; max-age=" + vEnd;
          break;
        case String:
          sExpires = "; expires=" + vEnd;
          break;
        case Date:
          sExpires = "; expires=" + vEnd.toUTCString();
          break;
      }
    }
    if(escape !== false){
    	sValue = encodeURIComponent(sValue);
    }
    document.cookie = encodeURIComponent(sKey) + "=" + sValue + sExpires + (sDomain ? "; domain=" + sDomain : "") + (sPath ? "; path=" + sPath : "") + (bSecure ? "; secure" : "");
    return true;
  },
  removeItem: function (sKey, sPath, sDomain) {
    if (!this.hasItem(sKey)) { return false; }
    document.cookie = encodeURIComponent(sKey) + "=; expires=Thu, 01 Jan 1970 00:00:00 GMT" + (sDomain ? "; domain=" + sDomain : "") + (sPath ? "; path=" + sPath : "");
    return true;
  },
  hasItem: function (sKey) {
    if (!sKey) { return false; }
    return (new RegExp("(?:^|;\\s*)" + encodeURIComponent(sKey).replace(/[\-\.\+\*]/g, "\\$&") + "\\s*\\=")).test(document.cookie);
  },
  keys: function () {
    var aKeys = document.cookie.replace(/((?:^|\s*;)[^\=]+)(?=;|$)|^\s*|\s*(?:\=[^;]*)?(?:\1|$)/g, "").split(/\s*(?:\=[^;]*)?;\s*/);
    for (var nLen = aKeys.length, nIdx = 0; nIdx < nLen; nIdx++) { aKeys[nIdx] = decodeURIComponent(aKeys[nIdx]); }
    return aKeys;
  }
};

function Control(){
	this._last_id = 0;
	this._promises = {};
	this._client_id = this._uid();
	this._user = {%raw json_encode(current_user) %};
    this._pending_requests = [];
    this._send_timeout = null;
    this._broadcast = null;
    this._close = null;
}

Control.prototype.init = function(broadcast_callback, close_callback){
	this._broadcast = broadcast_callback;
	this._close = close_callback;
	return this._connect();
};

Control.prototype._connect = function(){
	return new Promise(function(resolve,reject){
		var ws = null;
		try{
			ws = new WebSocket('{{ ws_url }}' + "?client_id="+this._client_id);
		}
		catch(err){
			reject(err);
		}
		ws.onopen = function(){
			this._connection = ws;
			this._flush_pending();
			resolve('open');
		}.bind(this);
		ws.onmessage = function(evt){
			var message = JSON.parse(evt.data);
			if(message.cookie){
	            var expires = new Date();
	            expires.setMonth(expires.getMonth() + 1);
	            docCookies.setItem(message.cookie_name,
	            		message.cookie, expires.toGMTString(),'/',document.domain,null,false);
	            if(this._broadcast){
	            	this._broadcast('micro-cookie-set', message.result);
	            }
			}
			if(this._promises[message.id]){
				if(message.error){
					this._promises[message.id].reject(message);
				} else {
					this._promises[message.id].resolve(message.result);
				}
				delete this._promises[message.id];
			} else if(message.signal, this._broadcast){
				this._broadcast(message.signal, message.message);
			} else {
				console.log(message);
			}
		}.bind(this);
		ws.onclose = function(){
			this._connection = null;
			setTimeout(function(){
				if(this._close){
					this._close("closed");
				} else {
					location.reload(true);
				}
			}.bind(this), 200);
		}.bind(this);
		ws.onerror = function(err){
			if(!this._connection){
				reject(err.code || 'unknown error');
			}
		}.bind(this);
	}.bind(this));
};

Control.prototype._uid = function(){
    function _p8(s) {
        var p = (Math.random().toString(16)+"000000000").substr(2,8);
        return s ? "-" + p.substr(0,4) + "-" + p.substr(4,4) : p ;
    }
    return _p8() + _p8(true);
};

Control.prototype._flush_pending = function(){
    this._send_timeout = null;
    this._connection.send(JSON.stringify({requests: this._pending_requests}));
	this._pending_requests.length=0;
};

Control.prototype._send = function(action, args) {
	var id = this._client_id + ":"+ ++this._last_id;
	return new Promise(function(resolve,reject){
		this._pending_requests.push([id,action,args]);
        if (!this._send_timeout && this._connection) {
            this._send_timeout = setTimeout(this._flush_pending.bind(this), 0);
        }
		this._promises[id] = { reject: reject, resolve: resolve };
	}.bind(this));
};

{% for service in services %}
{% if service.docs and handler.settings.get('debug') is True %}/**
	{{ service.docs }}
**/{% end %}
Control.prototype.{{ service.name }} = function({{ ", ".join([p.name for p in service.desc.parameters.values() if p.name[0] != '_' and p.name != 'context']) }}){
	return this._send("{{ service.name }}", {
		{{ ",\n\t\t".join(["{0!r}: {0} {1}".format(p.name,'|| ' + json_encode(p.default) if p.default is not p.empty else '') for p in service.desc.parameters.values() if p.name[0] != '_' and p.name != 'context']) }}
	});
};
{% end %}
