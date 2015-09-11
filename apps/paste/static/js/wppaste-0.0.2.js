/*  Welborn Productions - Paste - Tools
    Client side utilities for loading/submitting pastes.
*/

/*  JSHint/JSLint options.
    `ace` and `wptools` are read-only globals.

    global ace:false, wptools:false
    global wp_modelist:true, wp_themelist:true, wp_content:true
*/

var wppaste = {
    // Modules and file names are versioned to "break" the cache on updates.
    version: '0.0.2',
    build_lang_menu : function () {
        /* Build language options. */
        $('#langselect').append(
            wppaste.build_menu(
                wp_modelist.modes,
                'mode',
                'caption'
            )
        );
    },

    build_menu : function (items, value, text) {
        /*  Build a select menu from an array of objects.
            Returns a jQuery object containing the built doc fragment.
            Arguments:
                items   : Array of objects to build from.
                value   : Object attribute for option value.
                text    : Object attribute for option text.
                          The list is sorted by this attribute.
        */

        items.sort(function (a, b) {
            // Sort items by 'caption' text
            if (a[text] < b[text]) {
                return -1;
            }
            if (a[text] > b[text]) {
                return 1;
            }
            return 0;

        });

        // create a doc fragment to build on.
        var $menufrag = $(document.createDocumentFragment());

        // create a None mode, should be at the top.
        var $noneitem = $(document.createElement('option'));
        $noneitem.attr({'val': ''});
        $noneitem.text('[none]');
        $menufrag.append($noneitem);

        // iterate over all known items.
        var objcurrent,
            $opt;
        var i = 0;
        for (i; i < items.length; i++) {
            // get mode info.
            objcurrent = items[i];
            // create an <option> element.
            $opt = $(document.createElement('option'));
            $opt.attr({'val': objcurrent[value]});
            $opt.text(objcurrent[text]);
            // add the new option to doc fragment.
            $menufrag.append($opt);
        }
        // Return whole menu fragment.
        return $menufrag;
    },

    build_theme_menu : function () {
        /* Build theme options */
        // Grab the list of themes and sort them by caption.
        $('#themeselect').append(
            wppaste.build_menu(
                wp_themelist.themes,
                'theme',
                'caption'
            )
        )
    },

    fix_line_breaks : function (size) {
        /* Fix line breaks in current paste content.
            Line breaks are added to lines longer than 80 chars.
            This will break code formatting! (meant to be used on data/text)
        */
        var content = wp_content.getValue();
        if (!content) {
            return false;
        }
        var chunksize = size || 80;
        var chunks = wppaste.split_string(content, chunksize);
        wp_content.getSession().setValue(chunks.join('\n'));
        return true;
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
        var $selected = $(langselect.options[langselect.selectedIndex]);
        return $selected.text();
    },

    get_selected_mode : function () {
        /* Get selected ace-editor mode. ('ace/mode/python') */
        var langselect = document.getElementById('langselect');
        var $selected = $(langselect.options[langselect.selectedIndex]);
        return $selected.attr('val');
    },

    get_selected_onhold : function () {
        /* Get 'on hold' option selection. */
        var chk = document.getElementById('paste-onhold-opt');
        // This option is not always created. (only authenticated users see it)
        return chk === null ? false : $(chk).prop('checked');

    },

    get_selected_private : function () {
        /* Get 'private' option selection. */
        var $chk = $('#paste-private-opt');
        return $chk.prop('checked');
    },

    get_selected_theme : function () {
        /* Get selected ace-editor theme ('ace/theme/themename'). */
        var themeselect = document.getElementById('themeselect');
        var $selected = $(themeselect.options[themeselect.selectedIndex]);
        return $selected.attr('val');
    },

    get_selected_theme_name : function () {
        /* Get selected ace-editor theme name ('Theme Name'). */
        var themeselect = document.getElementById('themeselect');
        var $selected = $(themeselect.options[themeselect.selectedIndex]);
        return $selected.text();
    },

    kill_message: function () {
        /* Remove the floater message immediately. */
        $('#floater').fadeOut();
    },

    load_paste_content: function () {
        /*  Loads the paste content from the #encoded-content.
            Content is Base64 encoded by the server, so it needs to be decoded.
        */
        var content = $('#encoded-content').text();
        if (content) {
            wp_content.getSession().setValue(Base64.decode(content));
        }
    },

    load_paste_settings: function (options) {
        /* Load user's paste settings from cookie. */
        var cookieraw = $.cookie('pastesettings');
        var author = '';
        var userlang = wptools.default_ace_langname || 'Python';
        var usertheme = wptools.default_ace_themename || 'Solarized Dark';
        var opts = options || {'nolangset': false};
        if (cookieraw) {
            var cookieinfo = JSON.parse(cookieraw);
            author = cookieinfo.author || '';
            userlang = cookieinfo.lang || userlang;
            usertheme = cookieinfo.theme || usertheme;
        }
        if (!opts.nolangset) {
            // set language from cookie
            wppaste.set_selected_mode(userlang);
        }
        // Set theme
        wppaste.set_selected_theme(usertheme);

        $('#paste-author-entry').val(author);
    },

    on_mode_change: function (opts) {
        /* Change Ace mode when language is selected.
            Arguments:
                opts  : object containing options for this functions.

                Options:
                    save : true/false to save the new mode to a cookie.
        */
        var modestr = wppaste.get_selected_mode();
        var session = wp_content.getSession();
        // Clear any error annotations that selecting a bad lang may have caused.
        session.clearAnnotations();
        // Set the new mode (causes re-highlighing)
        session.setMode(modestr);
        //console.log('mode set to: ' + modestr);

        // Save user language to a cookie for next time.
        if (opts && opts.save) {
            wppaste.update_paste_settings({'lang': wppaste.get_selected_lang()});
        }
    },

    on_theme_change: function (opts) {
        /* Change Ace theme when theme option is selected.
            Arguments:
                opts  : Object containing options for this function.
                    Options:
                        save : true/false, whether the theme is saved to a cookie.
        */
        var themestr = wppaste.get_selected_theme();
        wp_content.setTheme(themestr);
        //console.log('theme set to: ' + themestr);

        // Save user theme to a cookie for next time.
        if (opts && opts.save) {
            wppaste.update_paste_settings({'theme': wppaste.get_selected_theme_name()});
        }
    },

    save_paste_settings : function () {
        /* Save current UI settings to a cookie. */
        var cookieinfo = JSON.stringify({
            'lang': wppaste.get_selected_lang(),
            'author': wppaste.get_paste_author(),
            'theme': wppaste.get_selected_theme_name(),
        });

        return $.cookie('pastesettings', cookieinfo, {expires: 365, path: '/'});
    },

    set_editor_size: function (csssize) {
        /* Sets the size for the editor by setting the paste-content
           size and calling wp_content.resize().
        */
        if (csssize) {
            $('#paste-content').height(csssize);
            wp_content.resize();
        }
    },

    set_selected_mode : function (name) {
        /* set selected mode by name
            Arguments:
                name  : Name of mode to select.
        */
        var langselect = document.getElementById('langselect');
        var langlen = langselect.options.length;
        var i = 0;
        for (i; i < langlen; i++) {
            if (name === $(langselect.options[i]).text()) {
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

    set_selected_onhold : function (checked) {
        /* set selected 'onhold' option.
            Arguments:
                checked : true/false, whether onhold opt is checked.
        */
        var chk = document.getElementById('paste-onhold-opt');
        // This option is not always created. (only authenticated users see it)
        if (chk) {
            var boolval = checked || false;
            $(chk).attr({'checked': boolval});
        }
    },

    set_selected_private : function (checked) {
        /* set selected 'private' option.
            Arguments:
                checked  : true/false, whether the private opt. is checked.
        */

        var chk = document.getElementById('paste-private-opt');
        var boolval = checked || false;
        $(chk).attr({'checked': boolval});

    },

    set_selected_theme : function (name) {
        /* set selected theme by name. */
        var themeselect = document.getElementById('themeselect');
        var themelen = themeselect.options.length;
        var i = 0;
        for (i; i < themelen; i++) {
            if (name === $(themeselect.options[i]).text()) {
                themeselect.selectedIndex = i;
                wppaste.on_theme_change();
                return true;
            }
        }
        // no theme by that name.
        console.log('No theme named: "' + name + '"');
        themeselect.selectedIndex = 0;
        wppaste.on_theme_change();
        return false;
    },

    setup_ace: function (doreadonly) {
        /* Initial setup for ace editor.*/
        wp_content = ace.edit('paste-content');

        // various settings for ace
        wp_content.$blockScrolling = Infinity;
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
    },

    show_error_msg: function (message) {
        /* Show an error message by changing the floaters text and displaying it.
        */
        $('#floater-msg').html(message);
        wptools.center('#floater');

        $('#floater').fadeIn();
        setTimeout(function () { wppaste.kill_message(); }, 3000);
    },

    split_string: function (string, size) {
        var re = new RegExp('.{1,' + size + '}', 'g');
        return string.match(re);
    },

    submit_paste : function (existingdata) {
        // JSON data to send...
        var pastedata = existingdata || {};

        pastedata.author = wppaste.get_paste_author();
        pastedata.content = wp_content.getValue();
        pastedata.title = wppaste.get_paste_title();
        pastedata.language = wppaste.get_selected_lang();
        pastedata.onhold = wppaste.get_selected_onhold();
        /* jshint ignore: start */
        pastedata['private'] = wppaste.get_selected_private();
        /* jshint ignore: end */
        var replyto = $('#replyto-id').attr('value');
        pastedata.replyto = replyto;

        // Parse some of the user input.
        if (wptools.is_emptystr(pastedata.content)) {
            wppaste.show_error_msg('<span class="warning-msg">Paste must have some content.</span>');
            return false;
        }

        if (!pastedata.title) {
            // Set default title for pastes.
            pastedata.title = 'Untitled';
        }

        // change the loading message.
        wppaste.update_loading_msg('<span>Submitting paste...</span>');

        /*jslint unparam:true*/
        $.ajax({
            type: 'post',
            contentType: 'application/json',
            url: '/apps/paste/submit',
            data: JSON.stringify(pastedata),
            dataType: 'json',
            status: {
                404: function () { console.log('Page not found.'); },
                500: function () { console.log('A major error occurred.'); }
            }
        })
            .fail(function (xhr, status, err) {
                var msg = err.message || 'The error was unknown.';
                console.log('failure: ' + status + '\n    msg:' + msg);
                msg = 'An error occurred while submitting. ' + msg;
                wppaste.show_error_msg('<span class="warning-msg"> ' + msg + '</span>');
            })
            .done(function (data, status, xhr) {
                // handle errors...
                if (status === 'error') {
                    console.log('wp-error response: ' + xhr.responseText);
                    if (xhr.responseText) {
                        // This will probably be an ugly message.
                        wppaste.show_error_msg('<span class="warning-msg">' + xhr.responseText + '</span>');
                    }
                } else {
                    // Paste was successfully submitted.
                    var respdata = JSON.parse(xhr.responseText);

                    if (respdata.status && respdata.status === 'error') {
                        // App sent an error msg back.
                        wppaste.show_error_msg('<span class="warning-msg">' + respdata.message + '</span>');
                        console.log('error: ' + respdata.message);
                    } else {
                        // App sent back a success.
                        wppaste.submit_success(respdata);
                        // done loading success
                        $('#floater').fadeOut();
                    }


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
        if (!newdata) { return jsondata; }

        var oldobj = JSON.parse(jsondata);
        if (!oldobj) { return jsondata; }
        var newobj = wppaste.updateobject(oldobj, newdata);
        return JSON.stringify(newobj);
    },

    update_loading_msg: function (message) {
        /* Update floater message and size/position. */
        $('#floater-msg').html(message);
        wptools.center('#floater');
        $('#floater').fadeIn();
    },

    update_paste_settings : function (newsettings) {
        /* Update current cookie info with new keys/values,
           and save the cookie.

            Arguments:
                newsettings  : Object with json-friendly key/value pairs to
                               save as settings in the cookie.
        */

        var cookiejson = $.cookie('pastesettings');
        var settings = cookiejson ? JSON.parse(cookiejson) : {};


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

        if (!oldobj) { return newobj; }
        if (!newobj) { return oldobj; }

        // Make a shallow copy of the old object, so we don't modify it later.
        /*jslint forin:true*/
        var tmpobj = {};
        var oldkey;
        for (oldkey in oldobj) {
            if (tmpobj.hasOwnProperty(oldkey)) {
                tmpobj[oldkey] = oldobj[oldkey];
            }
        }

        // Iterate over all keys/values in the new object,
        // and update the old objects values.
        var newkey;
        for (newkey in newobj) {
            // See if the old key even exists.
            if (!tmpobj[newkey]) {
                // add the new key.
                tmpobj[newkey] = newobj[newkey];
            } else {
                // old key exists, make sure new value is good.
                if (newobj[newkey]) {
                    // new key is truthy, update the old one.
                    tmpobj[newkey] = newobj[newkey];
                }
                // otherwise the old key/value is kept.
            }
        }
        // return the modified old object.
        return tmpobj;
    }


};
