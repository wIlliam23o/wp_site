// Paste tools/helpers
var wppaste = {
    build_lang_menu : function () {
        /* Build language options. */
        var modelen = wp_modelist.modes.length;
        var modecur;
        var modeopt;
        // create a doc fragment to build on.
        var menufrag = document.createDocumentFragment();

        // create a None mode, should be at the top.
        var nonemode = document.createElement('option');
        $(nonemode).attr({'val': ''});
        $(nonemode).text('[none]');
        $(menufrag).append(nonemode);

        // iterate over all known modes.
        for (var i=0; i < modelen; i++) {
            // get mode info.
            modecur = wp_modelist.modes[i];
            // create an <option> element.
            modeopt = document.createElement('option');
            $(modeopt).attr({'val': modecur.mode});
            $(modeopt).text(modecur.name);
            // add the new option to doc fragment.
            $(menufrag).append(modeopt);
        }
        // Add whole menu fragment to the <select> tag.
        $('#langselect').append(menufrag);
    },

    get_mode_byname : function (name) {
        /* Get ace mode string by name. */
        var modestr = wp_modelist.modesByName[name];
        if (!modestr) {
            return '';
        } else {
            return modestr;
        }
    },

    get_paste_author : function () {
        /* not implemented yet. */
        return $('#paste-author-entry').val();
    },

    get_paste_title : function () {
        return $('#paste-title-entry').val();
    },

    get_selected_lang : function () {
        /* Get selected language name */
        var langselect = document.getElementById('langselect');
        var selected = langselect.options[langselect.selectedIndex];
        return $(selected).text();
    },

    get_selected_mode : function () {
        /* Get selected ace-editor mode. */
        var langselect = document.getElementById('langselect');
        var selected = langselect.options[langselect.selectedIndex];
        return $(selected).attr('val');
    },

    load_paste_settings : function (options) {
        /* Load user's paste settings from cookie. */
        var cookieraw = $.cookie('pastesettings');
        var author = '';
        var userlang = 'python';
        var opts = options || {'nolangset': false};
        if (cookieraw) {
            var cookieinfo = JSON.parse(cookieraw);
            author = cookieinfo.author || '';
            userlang = cookieinfo.lang || 'python';
        }
        if (!opts.nolangset) {
            // set language from cookie
            wppaste.set_selected_mode(userlang);
        }

        $('#paste-author-entry').val(author);
    },

    on_mode_change: function () {
        /* Change Ace mode when language is selected. */
        var modestr = wppaste.get_selected_mode();
        wp_content.getSession().setMode(modestr);
        //console.log('mode set to: ' + modestr);
    },

    set_selected_mode : function (name) {
        /* set selected mode by name */
        var langselect = document.getElementById('langselect');
        var langlen = langselect.options.length;
        for (var i=0; i < langlen; i++) {
            if (name == $(langselect.options[i]).text()) {
                langselect.selectedIndex = i;
                wppaste.on_mode_change();
                return true;
            }
        }
        // no mode by that name.
        langselect.selectedIndex = 0;
        wppaste.on_mode_change();
        return false;
    },

    submit_paste : function (existingdata) {
        // TODO: Think about, and implement, how a paste should be submitted,
        //       What kind of response, or redirect there should be.
        //       How to handle reply-tos/forks.
        //       Whether or not the paste is private/public
        //       Language preference.

        // JSON data to send...
        // TODO: Build suitable data for submitting a paste...
        if (existingdata) {
            var pastedata = existingdata;
        } else {
            var pastedata = {};
        }
        pastedata.author = wppaste.get_paste_author();
        pastedata.content = wp_content.getValue();
        pastedata.title = wppaste.get_paste_title();
        pastedata.language = wppaste.get_selected_lang();
        var replyto = $('#replyto-id').attr('value');
        pastedata.replyto = replyto

        // TODO: include 'onhold', make author textbox.

        // Parse some of the user input.
        if (wptools.is_emptystr(pastedata.content)) {
            show_error_msg('<span class="warning-msg">Paste must have some content.</span>');
            return false;
        }

        if (!pastedata.title) {
            // Set default title for pastes.
            pastedata.title = 'Untitled';
        }

        // change the loading message.
        update_loading_msg('<span>Submitting paste...</span>');
        
        $.ajax({
            type: 'post',
            contentType: 'application/json',
            url: '/apps/paste/submit',
            data: JSON.stringify(pastedata),
            dataType: 'json',
            failure: function (xhr, status, errorthrown) {
                console.log('failure: ' + status);
            },
            complete: function (xhr, status) {
                            
                // handle errors...
                if (status == 'error') {
                    // TODO: Handle errors. :)
                    console.log('wp-error response: ' + xhr.responseText);
                } else {
                    // Paste was successfully submitted.
                    // TODO: Decide what to do afterwards :)
                    var respdata = JSON.parse(xhr.responseText);

                    if (respdata.status && respdata.status === 'error') {
                        // Server sent an error msg back.
                        show_error_msg('<span class="warning-msg">' + respdata.message + '</span>');
                        console.log('error: ' + respdata.message);
                    } else {
                        // Server sent back a success.
                        wppaste.submit_success(respdata);
                        // done loading success
                        $('#floater').fadeOut();
                    }


                }

            },
            status: {
                404: function () { console.log('PAGE NOT FOUND!'); },
                500: function () { console.log('A major error occurred.'); }
            }
        });
    },

    submit_success : function (jsondata) {
        /* Called when the server sends back a successful json response. */
        if (jsondata.url) {
            // Good paste url returned, save a cookie with some info.
            var cookieinfo = JSON.stringify({
                'lang': wppaste.get_selected_lang(),
                'author': wppaste.get_paste_author(),
            });

            $.cookie('pastesettings', cookieinfo, {expires: 365, path:'/'});

            // Move to newly created paste.
            wptools.navigateto(jsondata.url);
        }
    }

};


// setup initial ace editor
function setup_ace (doreadonly) {
    wp_content = ace.edit('paste-content');
    // highlight style
    wp_content.setTheme('ace/theme/solarized_dark');
    // various settings for ace
    wp_content.setHighlightActiveLine(true);
    wp_content.setAnimatedScroll(true);
    wp_content.setFontSize(14);
    wp_content.getSession().setUseSoftTabs(true);
    // ensure read-only access to content
    if (doreadonly) {
        wp_content.setReadOnly(true);        
    }
    // Get mode list for ace. We will be using it later.
    wp_modelist = ace.require('ace/ext/modelist');

}

// update floater message and size/position
function update_loading_msg (message) {
    $('#floater-msg').html(message);
    wptools.center_element('#floater');
    var floater = $('#floater');
    var scrollpos = $(this).scrollTop();
    //floater.css({'top': scrollpos + 'px'});
    
    $('#floater').fadeIn();
}

function show_error_msg (message) {
    $('#floater-msg').html(message);
    wptools.center_element('#floater');
    var floater = $('#floater');
    var scrollpos = $(this).scrollTop();
    //floater.css({'top': scrollpos + 'px'});

    $('#floater').fadeIn();
    setTimeout(function () { kill_message(); }, 3000);
}

function kill_message () {
    /* Remove the floater message immediately. */
    $('#floater').fadeOut();
}