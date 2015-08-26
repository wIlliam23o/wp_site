/* Welborn Productions
    spam protection for email addresses.
        uses base64 to decode what content is in the href tag and possibly
        innerHTML of all wp-address selectors.
        you only need to be sure to base64 encode addresses before wrapping them
        in the wp-address class.
        ex:
            where mailto:cj@test.com = bWFpbHRvOmNqQHRlc3QuY29tCg==

            <a class='wp-address' href='bWFpbHRvOmNqQHRlc3QuY29tCg=='>
                Mail Me
            </a>
        ** can be any tag with the wp-address class.

    Debug button/box toggle added.
        shows/hides the django debug info box (for use with test site)


    Version: 0.2.0 (added safe native css selection, for future development)
             TODO: Use browserify to split some of this up, and rebundle it.
                   (easier development, pretty much the same deployment)

*/

/*  Some JSHint options:
    Allow browser globals, including console, and $ for jQuery.
    Allow a global 'use strict'.
*/
/* jshint browser:true, devel: true, jquery:true,globalstrict:true */

// Base64 is not linted, but is used in wptools. It should be read-only.
/* global Base64:false, ace:true */

'use strict';
var wptools = {
    // Default settings for code snippets, and when cookies are unavailable
    // for the Paste app.
    default_ace_langname: 'Python',
    default_ace_theme: 'ace/theme/solarized_dark',
    default_ace_themename: 'Solarized Dark',

    alert : function alert(msg, smallmsg) {
        /*  Show an alert message using #floater if available,
            otherwise use window.alert().
        */
        var $floater = $('#floater');
        if ($floater.length) {
            $('#floater-msg').html(msg);
            if (smallmsg) {
                $('#floater-smalltext').html(smallmsg);
            }
            $floater.fadeIn();
            wptools.center($floater, true);
            setTimeout(function () { $floater.fadeOut(); }, 5000);

        } else {
            // Fall-back to alert.
            if (smallmsg) {
                msg = msg + '\n\n' + smallmsg;
            }
            // Strip html-tags.
            window.alert($('<div>' + msg + '</div>').text());
        }
    },
    center: function center(selector, usevertical, useouter) {
        /*  Centers an element on screen.
            Arguments:
                selector     : jquery selector for elem.
                usevertical  : (bool)
                               center on vertical also.
                useouter     : (bool)
                               use window's outerHeight for vertical position.
        */

        var screen_width = $(document).width(),
            $elem = selector instanceof jQuery ? selector : $(selector),
            elempos = $elem.css('position'),
            elemy = -1,
            newx = -1,
            newy = -1,
            winheight = -1;

        if (!((elempos === 'fixed') || (elempos === 'absolute'))) {
            // Force the element to allow centering. If you have to do this
            // then something is wrong.
            $elem.css({'position': 'absolute'});
            console.log('Forced position:absolute on ' + $elem);
        }

        if ($elem && elempos) {
            // Horizontally
            newx = (screen_width - $elem.outerWidth()) / 2;
            $elem.css({'right': newx + 'px'});
            if (usevertical) {
                // Vertically
                elemy = $elem.outerHeight();
                winheight = useouter ? window.outerHeight : window.innerHeight;
                newy = (winheight - elemy) / 2;
                $elem.css({'top': newy + 'px'});
            }
        }
        return {'x': newx, 'y': newy};
    },

    csrf_safe_method : function csrf_safe_method(method) {
        /* Return true if this HTTP method name requires csrf protection. */
        // these HTTP methods do not require CSRF protection,
        // if it isn't one of these, it's okay.
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    },

    is_hidden : function is_hidden(selector_) {
        /* determines if element is hidden
         * by checking the display property */
        var box_display = $(selector_).css('display');
        return (box_display === '' || box_display === 'none');
    },

    is_address : function is_address(input_) {
        /* checks for email address */
        var regex_ = /^[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
        return input_.search(regex_) > -1;
    },

    is_emptystr : function is_emptystr(s) {
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

    is_mailto : function is_mailto(s) {
        /* checks for mailto: email address */
        var mailtopat = /^mailto:[\d\w\.]+@[\d\w\.]+.[\d\w\.]+$/;
        return s.search(mailtopat) > -1;
    },

    has_localstorage : function has_localstorage() {
        /* Determine if the current browser supports localStorage. */
        try {
            return window.hasOwnProperty('localStorage') && (window.localStorage !== null);
        } catch (e) {
            return false;
        }
    },

    hide_debug : function hide_debug() {
        /* Hides the debug box and changes it's label text. */
        $('.debug-box').hide();
        $('.debug-button-text').text('show debug');
    },

    load_css : function load_css(href) {
        /* Dynamically load a css file. */
        var link = document.createElement('link');
        link.href = href;
        link.type = 'text/css';
        link.rel = 'stylesheet';
        var head = document.getElementsByTagName('head')[0];
        head.appendChild(link);
    },

    navigateto : function navigateto(url) {
        window.location.href = url;
    },

    pre_ajax : function pre_ajax() {
        /*  Set global options for jQuery.ajax using $.ajaxSetup
            Django needs it's csrftoken cookie for all requests.
        */
        // This cookie is needed for Django.
        var csrftoken = $.cookie('csrftoken');
        // Build a dict of options and return it.
        var settings = {
            crossDomain: false,
            beforeSend: function (xhr, settings) {
                if (!wptools.csrf_safe_method(settings.type)) {
                    xhr.setRequestHeader('X-CSRFToken', csrftoken);
                }
            }
        };

        $.ajaxSettings.traditional = true;
        $.ajaxSetup(settings);
    },

    scroll_element : function scroll_element(selector, toppos) {
        if (!toppos) { toppos = 0; }
        var $elem = selector instanceof jQuery ? selector : $(selector),
            elpos = $elem.offset().top;
        $(window).scroll(function () {
            if (!wptools.element_is_hidden(selector)) {
                var y = $(this).scrollTop();
                if (y < elpos) {
                    $elem.stop().animate({'top': toppos}, 500);
                } else {
                    $elem.stop().animate({'top': y - elpos}, 500);
                }
            }
        });
    },

    scroll_to_anchor: function scroll_to_anchor(selector, animatespeed) {
        /* Scroll down/up to a specific anchor. */
        var $elem = selector instanceof jQuery ? selector : $(selector);
        if ($elem) {
            var animspeed = animatespeed || 'slow';
            $('html,body').animate({scrollTop: $elem.offset().top}, animspeed);
        }
    },

    select : function select(selector, container) {
        /*  Native css selector that returns the first element found, or null.
            Arguments:
                selector   : CSS selector.
                container  : Node to start from. Default: document
        */
        if (typeof selector !== 'string') {
            return null;
        }
        return (container || document).querySelector(selector);
    },

    select_all : function select_all(selector, container) {
        /*  Native css selector that returns an array of all matching elements.
            Returns an empty array on failure.
            Arguments:
                selector       : (string) CSS selector.
                container  : Node to start from. Default: document
        */
        if (typeof selector !== 'string') {
            return [];
        }
        return (container || document).querySelectorAll(selector);
    },

    setup_ace_snippet: function (elementid, fileext) {
        // Grab initial text from element, before building ace.
        var $aceelem = $(document.getElementById(elementid));
        if (!$aceelem.length) {
            return;
        }
        var snippetencoded = $aceelem.text();
        var snippettext = '';
        // The initial text is Base64 encoded, to save formatting.
        if (snippetencoded) {
            snippettext = Base64.decode($aceelem.text());
        }

        // Initialize the editor.
        var aceeditor = ace.edit(elementid);
        // Disabled ace scrolling to new selected text.
        aceeditor.$blockScrolling = Infinity;

        // highlight style
        aceeditor.setTheme(wptools.default_ace_theme);
        // various settings for ace
        aceeditor.setAnimatedScroll(true);
        aceeditor.setFontSize(14);
        // ensure read-only access to content
        aceeditor.setReadOnly(true);

        // get file mode for ace based on filename.
        var acemodelist = ace.require('ace/ext/modelist');
        var ace_mode = acemodelist.getModeForPath(fileext || '.txt');
        var ace_session = aceeditor.getSession();
        ace_session.setMode(ace_mode.mode || 'ace/mode/text');
        // Set text from initial element text.
        aceeditor.setValue(snippettext);

        // Move selection to start.
        ace_session.getSelection().selectFileStart();

        // Used to determine multiline options and height.
        var doclength = ace_session.getDocument().getLength();

        // Options depending on single line or multiline.
        var multilineopts = (doclength !== 1);
        aceeditor.renderer.setShowGutter(multilineopts);

        // Fix height for this snippet.
        // Keep small snippets small, but cap the height at whatever css is
        // set already.
        var lineheight = $aceelem.find('.ace_gutter-cell').css('height');
        if (doclength && lineheight) {
            var lineactual = parseInt(lineheight.replace(/px/, ''), 10);
            if (!isNaN(lineactual)) {
                var newheight = doclength * lineactual;
                if (newheight && (!isNaN(newheight)) && (newheight < 340)) {
                    $aceelem.css({'height': newheight + 2 + 'px'});
                }
            }
        }
        $aceelem.animate({'opacity': 1});
    },

    show_debug : function show_debug() {
        /* Displays the debug box and changes it's label text. */
        $('.debug-box').show();
        $('.debug-button-text').text('hide debug');
    },

    strdup : function strdup(char_, count_) {
        var s = '',
            i = 0;
        if (count_ && count_ > 0) {
            for (i; i < count_; i++) {
                s = s + char_;
            }
        }
        return s;
    },

    toggle_debug : function toggle_debug() {
        /*  Toggles debug-box between shown and hidden.
            This also changes the label text for it through
            show_debug() and hide_debug().
        */
        var $debugbox = $('.debug-box');
        if (wptools.is_hidden($debugbox)) {
            wptools.show_debug();
        } else {
            wptools.hide_debug();
        }

    },

    trim_whitespace : function trim_whitespace(s) {
        /* Trim all whitespace from a string. */
        if (s.replace) {
            return s.replace(/\s/g, '');
        }
        // not a string.
        return s;
    },

    vertical_element : function vertical_element(selector, toppos) {
        if (!toppos) { toppos = 0; }
        var $elem = selector instanceof jQuery ? selector : $(selector),
            y = $(this).scrollTop();
        if ($elem.length > 1) {
            $elem = $elem.get(0);
        }
        $elem.css({'top': y + toppos + 'px' });
    },

    wpaddress : function wpaddress(s) {
        /* decodes base64 email and mailto if base64 is present,
         * otherwise returns original string */
        var decoded = Base64.decode(s).replace('\n', '');
        if (this.is_address(decoded) || this.is_mailto(decoded)) {
            return decoded;
        }
        return s;
    },

    wpreveal : function wpreveal(selector) {
        /*  Reveals all base64 encoded mailto: and
            email addresses with selector
        */
        // use default welbornprod address class if no selector is passed.
        selector = selector || '.wp-address';
        var elems = document.querySelectorAll(selector);
        var length = elems.length;
        var i = 0;
        var href, target;
        //var i=0;
        if (length > 0) {
            for (i; i < length; i++) {
               // fix href target
                href = elems[i].getAttribute('href');
                if (href) {
                    target = href.valueOf();
                    if (target) {
                        elems[i].setAttribute('href', this.wpaddress(target));
                    }
                }
                // fix inner html..
                //elems[i].innerHTML = this.wpaddress(elems[i].innerHTML);
                var $e = $(elems[i]);
                $e.html(this.wpaddress($e.html()));
            }
        }
        return true;
    }


};

/* ------------------------------------------------------------------------- */

/* Various tools for Misc section
    ..instead of adding yet another file for this small amount of code.
      it is kept here in the 'global' utilities. If the code ever grows
      beyond these few things it may be moved to its own file in misc/static/js
*/
var misctools = {
    fixLongDescBtn: function fixLongDescBtn(alias) {
        var miscbtnid = '#misclongdescbtn-' + alias;
        var $longdescbtn = $(miscbtnid);

        if ($longdescbtn.text() === 'Show Less') {
            // element is hidden
            $longdescbtn.text('Show More');
        } else {
            $longdescbtn.text('Show Less');
        }
    },

    submitMisc: function submitMisc(f) {
        $('#viewer-filename').val(f);
        $('#file-viewer').submit();
    },

    toggleLongDesc: function toggleLongDesc(alias) {
        $('#misclongdesc-' + alias).slideToggle();
        $('#miscusage-' + alias).slideToggle();
        this.fixLongDescBtn(alias);
    }
};


/* ------------------------------------------------------------------------- */

/**
*
*  Base64 encode / decode
*  http://www.webtoolkit.info/
*
**/

/* jshint ignore:start */
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

            if (enc3 !== 64) {
                output = output + String.fromCharCode(chr2);
            }
            if (enc4 !== 64) {
                output = output + String.fromCharCode(chr3);
            }

        }
        output = Base64._utf8_decode(output);
        return output;
    },

    // private method for UTF-8 encoding
    _utf8_encode : function (string) {
        string = string.replace(/\r\n/g, '\n');
        var utftext = '',
            n = 0,
            c;

        for (n; n < string.length; n++) {
            c = string.charCodeAt(n);

            if (c < 128) {
                utftext += String.fromCharCode(c);
            } else if ((c > 127) && (c < 2048)) {
                utftext += String.fromCharCode((c >> 6) | 192);
                utftext += String.fromCharCode((c & 63) | 128);
            } else {
                utftext += String.fromCharCode((c >> 12) | 224);
                utftext += String.fromCharCode(((c >> 6) & 63) | 128);
                utftext += String.fromCharCode((c & 63) | 128);
            }

        }

        return utftext;
    },

    // private method for UTF-8 decoding
    _utf8_decode : function (utftext) {
        var string = '',
            i = 0,
            c = 0,
            c2 = 0,
            c3 = 0;
        while (i < utftext.length) {

            c = utftext.charCodeAt(i);

            if (c < 128) {
                string += String.fromCharCode(c);
                i++;
            } else if ((c > 191) && (c < 224)) {
                c2 = utftext.charCodeAt(i + 1);
                string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
                i += 2;
            } else {
                c2 = utftext.charCodeAt(i + 1);
                c3 = utftext.charCodeAt(i + 2);
                string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
                i += 3;
            }
        }

        return string;
    }
};

/* jshint ignore:end */

/* ------------------------------------------------------------------------- */

/* Rotator settings specific to welbornprod.... */
var wprotator_settings = {
    width: '100%',
    height: 300,
    thumb_width: 24,
    thumb_height: 24,
    button_width: 24,
    button_height: 24,
    button_margin: 5,
    auto_start: true,
    delay: 5000,
    play_once: false,
    transition: 'fade',
    transition_speed: 1000,
    auto_center: true,
    easing: 'easeInBack',
    cpanel_position: 'inside',
    cpanel_align: 'BL',
    timer_align: 'top',
    display_thumbs: true,
    display_dbuttons: true,
    display_playbutton: true,
    display_thumbimg: false,
    display_side_buttons: false,
    display_numbers: true,
    display_timer: true,
    mouseover_select: false,
    mouseover_pause: true,
    cpanel_mouseover: true,
    text_mouseover: false,
    text_effect: 'fade',
    text_sync: false,
    tooltip_type: 'none',
    shuffle: false,
    block_size: 75,
    vert_size: 55,
    horz_size: 50,
    block_delay: 25,
    vstripe_delay: 75,
    hstripe_delay: 180
};
