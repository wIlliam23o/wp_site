/* Welborn Productions
    spam protection for email addresses.
    uses base64 to decode what content is in the href tag and possibly
    innerHTML of all wp-address selectors.
    you only need to be sure to base64 encode addresses before wrapping them
    in the wp-address class.
    ex:
        mailto:cj@test.com = bWFpbHRvOmNqQHRlc3QuY29tCg==
        
        <a class='wp-address' href="bWFpbHRvOmNqQHRlc3QuY29tCg==">Mail Me</a>
    or:
    
        mailto:cj@welbornprod.com = bWFpbHRvOmNqQHdlbGJvcm5wcm9kLmNvbQo=
        cj@welbornprod.com = Y2pAd2VsYm9ybnByb2QuY29tCg==
        
        <a class='wp-address' href="bWFpbHRvOmNqQHdlbGJvcm5wcm9kLmNvbQo=">
            Y2pAd2VsYm9ybnByb2QuY29tCg==
        </a>
    
    ** can be any tag with the wp-address class.
*/

var wpTools = {
        wpreveal : function () {
                        var elems = document.querySelectorAll('.wp-address');
                        
                        var length = elems.length
                        if (length > 0) {
                            for (var i=0; i < length; i++) {
                                // fix href target
                                var href_ = elems[i].getAttribute('href');
                                if (href_) {
	                                var target_ = href_.valueOf();
	                                if (target_) {
	                                    elems[i].setAttribute('href', this.wpaddress(target_));
	                                }
                                }
                                // fix inner html..
                                elems[i].innerHTML = this.wpaddress(elems[i].innerHTML);
                            }
                        }
                        return true;
                    },

        wpaddress : function (input_) {
                        decoded_ = Base64.decode(input_).replace('\n', '');
                        if (this.is_address(decoded_) || this.is_mailto(decoded_)) {
                            return decoded_;
                        } else {
                            return input_;
                        }
                    },

        is_mailto : function (input_) {
                        regex_ = /^mailto:[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
                        return input_.search(regex_) > -1;
                    },

        is_address : function (input_) {
                        regex_ = /^[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
                        return input_.search(regex_) > -1;
                    },
        }
        
/**
*
*  Base64 encode / decode
*  http://www.webtoolkit.info/
*
**/
 
var Base64 = {
 
    // private property
    _keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
 
    // public method for encoding
    encode : function (input) {
        var output = "";
        var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
        var i = 0;
 
        input = Base64._utf8_encode(input);
 
        while (i < input.length) {
 
            chr1 = input.charCodeAt(i++);
            chr2 = input.charCodeAt(i++);
            chr3 = input.charCodeAt(i++);
 
            enc1 = chr1 >> 2;
            enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
            enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
            enc4 = chr3 & 63;
 
            if (isNaN(chr2)) {
                enc3 = enc4 = 64;
            } else if (isNaN(chr3)) {
                enc4 = 64;
            }
 
            output = output +
            this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
            this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);
 
        }
 
        return output;
    },
 
    // public method for decoding
    decode : function (input) {
        var output = "";
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;
 
        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
 
        while (i < input.length) {
 
            enc1 = this._keyStr.indexOf(input.charAt(i++));
            enc2 = this._keyStr.indexOf(input.charAt(i++));
            enc3 = this._keyStr.indexOf(input.charAt(i++));
            enc4 = this._keyStr.indexOf(input.charAt(i++));
 
            chr1 = (enc1 << 2) | (enc2 >> 4);
            chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
            chr3 = ((enc3 & 3) << 6) | enc4;
 
            output = output + String.fromCharCode(chr1);
 
            if (enc3 != 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 != 64) {
                output = output + String.fromCharCode(chr3);
            }
 
        }
 
        output = Base64._utf8_decode(output);
 
        return output;
 
    },
 
    // private method for UTF-8 encoding
    _utf8_encode : function (string) {
        string = string.replace(/\r\n/g,"\n");
        var utftext = "";
 
        for (var n = 0; n < string.length; n++) {
 
            var c = string.charCodeAt(n);
 
            if (c < 128) {
                utftext += String.fromCharCode(c);
            }
            else if((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            }
            else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }
 
        }
 
        return utftext;
    },
 
    // private method for UTF-8 decoding
    _utf8_decode : function (utftext) {
        var string = "";
        var i = 0;
        var c = c1 = c2 = 0;
 
        while ( i < utftext.length ) {
 
            c = utftext.charCodeAt(i);
 
            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            }
            else if((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i+1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            }
            else {
                c2 = utftext.charCodeAt(i+1);
                c3 = utftext.charCodeAt(i+2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
 
        }
 
        return string;
    }
 
}