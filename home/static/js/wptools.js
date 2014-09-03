/* Welborn Productions
    spam protection for email addresses.
        uses base64 to decode what content is in the href tag and possibly
        innerHTML of all wp-address selectors.
        you only need to be sure to base64 encode addresses before wrapping them
        in the wp-address class.
        ex:
            where mailto:cj@test.com = bWFpbHRvOmNqQHRlc3QuY29tCg==

            <a class='wp-address' href='bWFpbHRvOmNqQHRlc3QuY29tCg=='>Mail Me</a>
        or:

            where mailto:cj@welbornprod.com = bWFpbHRvOmNqQHdlbGJvcm5wcm9kLmNvbQo=
            and cj@welbornprod.com = Y2pAd2VsYm9ybnByb2QuY29tCg==

            <a class='wp-address' href='bWFpbHRvOmNqQHdlbGJvcm5wcm9kLmNvbQo='>
                Y2pAd2VsYm9ybnByb2QuY29tCg==
            </a>

        ** can be any tag with the wp-address class.

    Debug button/box toggle added.
        shows/hides the django debug info box (for use with test site)

*/

var wptools = {
    center: function (selector, usevertical) {
        /*  Centers an element on screen.
            Arguments:
                selector     : selector for elem.
                usevertical  : (true/false) center on vertical also.
        */
        var screen_width = $(document).width();
        var elem = $(selector);
        var newx = -1;
        var newy = -1;
        if (elem) {
            newx = (screen_width - elem.width()) / 2;
            $(selector).css({'right': newx + 'px'});
            if (usevertical) {
                newy = (window.innerHeight / 2) - elem.height();
                elem.css({'top': newy + 'px'});
            }
        }
        return {'x': newx, 'y': newy};
    },

    csrf_safe_method : function (method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    },

    flow_surround : function () {
        /* Flows the page surround around the vertical menu when needed. */
        if ($(window).width() < 800) {
            if (!wptools.squeezed) {
                wptools.squeezed = true;
                $('#page-surround').css({'margin-left': '20px'});
            }
        } else {
            if (wptools.squeezed) {
                wptools.squeezed = false;
                $('#page-surround').css({'margin-left': '0px'});
            }
        }
    },

    is_hidden : function(selector_) {
        /* determines if element is hidden
         * by checking the display property */
        var box_display = $(selector_).css('display');
        return (box_display === '' || box_display == 'none');
    },

    is_address : function (input_) {
        /* checks for email address */
        var regex_ = /^[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
        return input_.search(regex_) > -1;
    },

    is_emptystr : function (s) {
        if (s) {
            // we have a string or something. Try replacing whitespace.
            if (s.replace && (s.replace(/\s/g, '') === '')) {
                // It was an empty string (whitespace doesn't count)
                return true;
            }
        } else {
            if (!s) {
                // Falsey values pass as empty string.
                return true;
            }
        }
        // Was not empty string, or it is some other truthy object.
        return false;
    },

    is_mailto : function (input_) {
        /* checks for mailto: email address */
        var regex_ = /^mailto:[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
        return input_.search(regex_) > -1;
    },

    has_localstorage : function () {
        /* Determine if the current browser supports localStorage. */
        try {
            return ('localStorage' in window) && (window['localStorage'] != null);
        } catch (e) {
            return false;
        }
    },

    hide_debug : function () {
        /* Hides the debug box and changes it's label text. */
        $('.debug-box').hide();
        $('.debug-button-text').text('show debug');
    },

    navigateto : function (url) {
        window.location.href = url;
    },

	pre_ajax : function () {
		/*  Set global options for jQuery.ajax using $.ajaxSetup
            Django needs it's csrftoken cookie for all requests.
        */
        // This cookie is needed for Django.
        var csrftoken = $.cookie('csrftoken');
        // Build a dict of options and return it.
        var settings = {
            crossDomain: false,
            beforeSend: function(xhr, settings) {
                if (!wptools.csrf_safe_method(settings.type)) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            }
        };

		$.ajaxSettings.traditional = true;
		$.ajaxSetup(settings);
	},

	scroll_element : function (selector, toppos) {
		if (!toppos) { toppos = 0; }
		var el=$(selector);
		var elpos=el.offset().top;
		$(window).scroll(function () {
			if (!wptools.element_is_hidden(selector)) {
				var y=$(this).scrollTop();
				if(y<elpos){el.stop().animate({'top': toppos},500);}
				else{el.stop().animate({'top':y-elpos},500);}
			}
		});
	},

    scroll_to_anchor: function (selector, animatespeed) {
        /* Scroll down/up to a specific anchor. */
        var elem = $(selector);
        if (elem) {
            var animspeed = animatespeed || 'slow';
            $('html,body').animate({scrollTop: elem.offset().top}, animspeed)
        }
    },

    show_debug : function () {
        /* Displays the debug box and changes it's label text. */
        $('.debug-box').show();
        $('.debug-button-text').text('hide debug');
    },

    // Whether or not the window has been squeezed (< 800px) yet.
    squeezed: false,

    strdup : function (char_, count_ ) {
        var s = '';
        if (count_ && count_ > 0) {
            for (i=0; i < count_; i++) {
                s = s + char_;
            }
        }
        return s;
    },

    toggle_debug : function () {
        /*  Toggles debug-box between shown and hidden.
            This also changes the label text for it through
            show_debug() and hide_debug().
        */
        var debugbox = $('.debug-box');
        if (wptools.is_hidden(debugbox)) {
            wptools.show_debug();
        } else {
            wptools.hide_debug();
        }

    },

    trim_whitespace : function (s) {
        /* Trim all whitespace from a string. */
        if (s.replace) {
            return s.replace(/\s/g, '');
        }
        // not a string.
        return s;
    },

	vertical_element : function (selector, toppos) {
		if (!toppos) { toppos = 0; }
		var elem = $(selector);
		if (elem.length > 1) {
            elem = elem[0];
        }
		var y = $(this).scrollTop();
		elem.css({'top': y + toppos + 'px' });
	},

    wpaddress : function (input_) {
        /* decodes base64 email and mailto if base64 is present,
         * otherwise returns original string */
        var decoded_ = Base64.decode(input_).replace('\n', '');
        if (this.is_address(decoded_) || this.is_mailto(decoded_)) {
            return decoded_;
        } else {
            return input_;
        }
          },

    wpreveal : function (selector) {
        /* Reveals all base64 encoded mailto: and
         * email addresses with selector */
        // use default welbornprod address class if no selector is passed.
        if (!selector) { selector = '.wp-address'; }
        var elems = document.querySelectorAll(selector);

        var length = elems.length;
        //var i=0;
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
                //elems[i].innerHTML = this.wpaddress(elems[i].innerHTML);
                $(elems[i]).html(this.wpaddress($(elems[i]).html()));
            }
        }
        return true;
    }


};

/* Various tools for Misc section
    ..instead of adding yet another file for this small amount of code.
      it is kept here in the 'global' utilities. If the code ever grows
      beyond these few things it may be moved to its own file in misc/static/js
*/
var misctools = {
    fixLongDescBtn: function (alias) {
        var miscbtnid = '#misclongdescbtn-' + alias;
        var longdescbtn = $(miscbtnid);

        if (longdescbtn.text() == 'Show Less') {
            // element is hidden
            longdescbtn.text('Show More');
        } else {
            longdescbtn.text('Show Less');
        }
    },

    submitMisc: function (f) {
        $('#viewer-filename').val(f);
        $('#file-viewer').submit();
    },

    toggleLongDesc: function (alias) {
        var longdescid = '#misclongdesc-' + alias;
        var longdesc = $(longdescid);
        longdesc.slideToggle();
        this.fixLongDescBtn(alias);
    }
};


/**
*
*  Base64 encode / decode
*  http://www.webtoolkit.info/
*
**/
var Base64 = {

    // private property
    _keyStr : 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=',

    // public method for encoding
    encode : function (input) {
        var output = '';
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
        var output = '';
        var chr1, chr2, chr3;
        var enc1, enc2, enc3, enc4;
        var i = 0;

        input = input.replace(/[^A-Za-z0-9\+\/\=]/g, '');

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
        string = string.replace(/\r\n/g,'\n');
        var utftext = '';

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
        var string = '';
        var i = 0;
        var c = 0;
        var c1 = 0;
        var c2 = 0;
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
};

/* Rotator settings specific to welbornprod.... */
var wprotator_settings = {
	width:'100%',
	height:300,
	thumb_width:24,
	thumb_height:24,
	button_width:24,
	button_height:24,
	button_margin:5,
	auto_start:true,
	delay:5000,
	play_once:false,
	transition:'fade',
	transition_speed:1000,
	auto_center:true,
	easing:'easeInBack',
	cpanel_position:'inside',
	cpanel_align:'BL',
	timer_align:'top',
	display_thumbs:true,
	display_dbuttons:true,
	display_playbutton:true,
	display_thumbimg:false,
	display_side_buttons:false,
	display_numbers:true,
	display_timer:true,
	mouseover_select:false,
	mouseover_pause:true,
	cpanel_mouseover:true,
	text_mouseover:false,
	text_effect:'fade',
	text_sync:false,
	tooltip_type:'none',
	shuffle:false,
	block_size:75,
	vert_size:55,
	horz_size:50,
	block_delay:25,
	vstripe_delay:75,
	hstripe_delay:180
};
