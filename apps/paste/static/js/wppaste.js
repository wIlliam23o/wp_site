// Paste tools/helpers
var wppaste = {
    build_lang_menu : function () {
        /* Build language options. */
        var modes = wp_modelist.modes;
        modes.sort(function (a, b) {
            // Sort modes by 'caption' text
            if (a.caption < b.caption) {
                return -1
            } else if (a.caption > b.caption) {
                return 1
            } else {
                return 0
            }
        });
        // create a doc fragment to build on.
        var menufrag = document.createDocumentFragment();

        // create a None mode, should be at the top.
        var nonemode = document.createElement('option');
        $(nonemode).attr({'val': ''});
        $(nonemode).text('[none]');
        $(menufrag).append(nonemode);

        // iterate over all known modes.
        var modecur;
        var modeopt;
        for (var i=0; i < modes.length; i++) {
            // get mode info.
            modecur = modes[i];
            // create an <option> element.
            modeopt = document.createElement('option');
            $(modeopt).attr({'val': modecur.mode});
            $(modeopt).text(modecur.caption);
            // add the new option to doc fragment.
            $(menufrag).append(modeopt);
        }
        // Add whole menu fragment to the <select> tag.
        $('#langselect').append(menufrag);
    },

    build_theme_menu : function () {
        /* Build theme options */
        // Grab the list of themes and sort them by caption.
        var themes = wp_themelist.themes;
        themes.sort(function (a, b) {
            // sort the themes by 'caption' text.
            if (a.caption < b.caption) {
                return -1
            } else if (a.caption > b.caption) {
                return 1
            } else {
                return 0
            }
        });
        // Doc frag to build on.
        var themefrag = document.createDocumentFragment();
        // iterate over all known themes.
        var themecur;
        var themeopt;
        for (var i=0; i < themes.length; i++) {
            // get theme info.
            themecur = wp_themelist.themes[i];
            // create an <option>
            themeopt = document.createElement('option');
            $(themeopt).attr({'val': themecur.theme});
            $(themeopt).text(themecur.caption);
            // add option to the doc frag.
            $(themefrag).append(themeopt);
        }
        // Add whole theme-menu fragment to the <select> tag.
        $('#themeselect').append(themefrag);
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
        /* Get selected ace-editor mode. ('ace/mode/python') */
        var langselect = document.getElementById('langselect');
        var selected = langselect.options[langselect.selectedIndex];
        return $(selected).attr('val');
    },

    get_selected_theme : function () {
        /* Get selected ace-editor theme ('ace/theme/themename'). */
        var themeselect = document.getElementById('themeselect');
        var selected = themeselect.options[themeselect.selectedIndex];
        return $(selected).attr('val');
    },

    get_selected_theme_name : function () {
        /* Get selected ace-editor theme name ('Theme Name'). */
        var themeselect = document.getElementById('themeselect');
        var selected = themeselect.options[themeselect.selectedIndex];
        return $(selected).text();
    },

    load_paste_settings : function (options) {
        /* Load user's paste settings from cookie. */
        var cookieraw = $.cookie('pastesettings');
        var author = '';
        var userlang = 'Python';
        var usertheme = 'Solarized Dark';
        var opts = options || {'nolangset': false};
        if (cookieraw) {
            var cookieinfo = JSON.parse(cookieraw);
            author = cookieinfo.author || '';
            userlang = cookieinfo.lang || 'Python';
            usertheme = cookieinfo.theme || 'Solarized Dark';
        }
        if (!opts.nolangset) {
            // set language from cookie
            wppaste.set_selected_mode(userlang);
        }
        // Set theme
        wppaste.set_selected_theme(usertheme);

        $('#paste-author-entry').val(author);
    },

    on_mode_change: function () {
        /* Change Ace mode when language is selected. */
        var modestr = wppaste.get_selected_mode();
        wp_content.getSession().setMode(modestr);
        //console.log('mode set to: ' + modestr);

        // Save user language to a cookie for next time.
        wppaste.update_paste_settings({'lang': wppaste.get_selected_lang()});
    },

    on_theme_change: function () {
        /* Change Ace theme when theme option is selected. */
        var themestr = wppaste.get_selected_theme();
        wp_content.setTheme(themestr);
        //console.log('theme set to: ' + themestr);

        // Save user theme to a cookie for next time.
        wppaste.update_paste_settings({'theme': wppaste.get_selected_theme_name()});
    },

    save_paste_settings : function () {
        /* Save current UI settings to a cookie. */
        var cookieinfo = JSON.stringify({
            'lang': wppaste.get_selected_lang(),
            'author': wppaste.get_paste_author(),
            'theme': wppaste.get_selected_theme_name(),
        });

        return $.cookie('pastesettings', cookieinfo, {expires: 365, path:'/'});
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
        console.log('No mode named: "' + name + '"');
        langselect.selectedIndex = 0;
        wppaste.on_mode_change();
        return false;
    },

    set_selected_theme : function (name) {
        /* set selected theme by name. */
        var themeselect = document.getElementById('themeselect');
        var themelen = themeselect.options.length;
        for (var i=0; i < themelen; i++) {
            if (name == $(themeselect.options[i]).text()) {
                themeselect.selectedIndex = i;
                wppaste.on_theme_change();
                return true
            }
        }
        // no theme by that name.
        console.log('No theme named: "' + name + '"');
        themeselect.selectedIndex = 0;
        wppaste.on_theme_change();
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
            wppaste.save_paste_settings();

            // Move to newly created paste.
            wptools.navigateto(jsondata.url);
        }
    },

    updatejson : function (jsondata, newdata) {
        /* Update JSON object data with new keys/values.
            Arguments:
                jsondata : JSON string with object inside.
                newdata  : object with keys/values to update.

            Returns updated JSON (Does not modify the original.)
        */
        
        if (!jsondata) { return JSON.stringify(newdata) || ''; }
        else if (!newdata) { return jsondata;}

        var oldobj = JSON.parse(jsondata);
        if (!oldobj) { return jsondata;}
        var newobj = wppaste.updateobject(oldobj, newdata);
        return JSON.stringify(newobj);
    },

    update_paste_settings : function (newsettings) {
        /* Update current cookie info with new keys/values,
           and save the cookie.

            Arguments:
                newsettings  : Object with json-friendly key/value pairs to
                               save as settings in the cookie.
        */

        var cookiejson = $.cookie('pastesettings');
        if (cookiejson) {
            var settings = JSON.parse(cookiejson);
        } else {
            var settings = {};
        }

        // update the old settings and convert to JSON
        var updated = wppaste.updateobject(settings, newsettings);
        var updatedjson = JSON.stringify(updated);

        // save updated settings to cookie.
        return $.cookie('pastesettings', updatedjson, {expires: 365, path: '/'});
    },


    updateobject : function (oldobj, newobj) {
        /* Update an object based on another objects values.
            Arguments:
                oldobj  : Old object to update with simple keys/values.
                newobj  : New object with keys/values to update with.

            Returns updated object, does not modify the original object.
        */

        if (!oldobj) { return newobj;}
        else if (!newobj) { return oldobj;}

        // Make a shallow copy of the old object, so we don't modify it later.
        var tmpobj = {};
        for (var oldkey in oldobj) {
            tmpobj[oldkey] = oldobj[oldkey];
        }

        // Iterate over all keys/values in the new object,
        // and update the old objects values.
        for (var newkey in newobj) {
            // See if the old key even exists.
            if (!tmpobj[newkey]) {
                // add the new key.
                tmpobj[newkey] = newobj[newkey];
            } else {
                // old key exists, make sure new value is good.
                if (newobj[newkey]) {
                    // new key is truthy, update the old one.
                    tmpobj[newkey] = newobj[newkey]
                } 
                // otherwise the old key/value is kept.
            }
        }
        // return the modified old object.
        return tmpobj
    }


};


// setup initial ace editor
function setup_ace (doreadonly) {
    wp_content = ace.edit('paste-content');
    // highlight style (set in load_paste_settings)
    //wp_content.setTheme('ace/theme/solarized_dark');
    // various settings for ace
    wp_content.setHighlightActiveLine(true);
    wp_content.setAnimatedScroll(true);
    wp_content.setFontSize(14);
    wp_content.getSession().setUseSoftTabs(true);
    // ensure read-only access to content
    if (doreadonly) {
        wp_content.setReadOnly(true);        
    }
    // Get mode/theme list for ace. We will be using them later.
    wp_modelist = ace.require('ace/ext/modelist');
    wppaste.build_lang_menu();
    wp_themelist = ace.require('ace/ext/themelist');
    wppaste.build_theme_menu();
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