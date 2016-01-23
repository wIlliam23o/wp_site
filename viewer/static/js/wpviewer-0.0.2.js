/* Welborn Productions - Viewer
   Handles file-viewer actions on the client side.
   - Christopher Welborn 2013 -desc added in 2014 :)
*/


/*    global ace:false, wptools:false */
/*    global wp_content:true, wp_modelist:true */

// Store current relative filename here. The template sends it on the first
// page load, and then it is set with JS when doing ajax calls.
var wpviewer = {
    // Modules and file names are versioned to "break" the cache on updates.
    version: '0.0.2',
    // current relative path for file. (/static/file.py)
    current_file : '',
    // current short name (file.py)
    current_name : '',

    change_content: function (s) {
        /* Change ace editor content, move selection to start. */
        wp_content.setValue(s);
        wp_content.selection.selectFileStart();
    },

    enable_link : function (linkelem, enabled) {
        /* Make a menu item enabled/disabled */
        var $link = linkelem instanceof jQuery ? linkelem : $(linkelem);
        var $linkitem = $link.children(),
            menutarget = $link.attr('onclick');
        if (!menutarget) {
            console.log('can\'t find href for element: ' + linkelem);
            return false;
        }
        // TODO: Just use event handlers. Set elem.click() to the proper
        //       function when enabled, and to a dummy when disabled.
        if (enabled) {
            // ensure this link is 'enabled'
            if (menutarget.indexOf('false') < 0) {
                // change 'false' to 'true' because view_file(filename, true)
                // means 'do not load this file', cancel = true
                $link.attr('onclick', menutarget.replace('true', 'false'));
                $link.removeClass('vertical-menu-item-disabled');
                $linkitem.removeClass('vertical-menu-item-disabled');
                return true;
            }
            // already enabled.
            return true;
        }

        // ensure this link is 'disabled' (true means disabled)
        if (menutarget.indexOf('true') < 0) {
            $link.attr('onclick', menutarget.replace('false', 'true'));
            $link.addClass('vertical-menu-item-disabled');
            $linkitem.addClass('vertical-menu-item-disabled');
            return true;
        }
        // already disabled.
        return true;
    },

    load_file_data: function (xhrdata) {
        var file_info = JSON.parse(xhrdata.responseText);

        var $filecontentbox = $('#file-content-box');
        // Server-side error.
        if (file_info.status === 'error') {
            var msg = file_info.message || 'Sorry, an unknown error occurred.';
            $filecontentbox.html('<span>' + msg + '</span>');
            return;
        }

        // Content
        if (file_info.file_content) {
            // Load content into ace editor...
            wpviewer.change_content(file_info.file_content);
            // Set Language
            var ace_mode = wp_modelist.getModeForPath(file_info.static_path);
            wp_content.getSession().setMode(ace_mode.mode);
            $('#file-content').fadeIn();

        } else {
            $filecontentbox.html('<span>Sorry, no content in this file...</span>');
            return;
        }

        /* Header for projects ...pythons None equates to null in JS. */
        if (file_info.project_alias !== null && file_info.project_name !== null) {
            $('#project-title-name').html(file_info.project_name);
            $('#project-link').click(function () { wptools.navigateto('/projects/' + file_info.project_alias); });
            if (file_info.project_alias) { $('#project-info').fadeIn(); }
        // Header for miscobj.
        } else if (file_info.misc_alias !== null && file_info.misc_name !== null) {
            $('#project-title-name').html(file_info.misc_name);
            $('#project-link').click(function () { wptools.navigateto('/misc/' + file_info.misc_alias); });
            if (file_info.misc_alias) { $('#project-info').fadeIn(); }
        }
        // File info
        if (file_info.file_short && file_info.static_path) {
            $('#viewer-filename').html(file_info.file_short);
            $('#file-link').click(function () { wptools.navigateto('/dl/' + file_info.static_path); });
            if (file_info.file_short) { $('#file-info').fadeIn(); }
            // set current working filename.
            wpviewer.set_current_file(file_info.static_path);
        }

        // Menu builder
        var menu_items = file_info.menu_items;
        if (menu_items) {
            var menu_length = menu_items.length,
                existing_length = $('.vertical-menu-item').length,
                menufilename,
                menuname;
            // Build the menu from scratch if this is the first load.
            if (existing_length === 0 && menu_length > 0) {
                var $menufrag = $(document.createDocumentFragment()),
                    $menuitem;
                $.each(menu_items, function () {
                    menufilename = this[0].replace(/[ ]/g, '/');
                    menuname = this[1];
                    var disabledval = 'false';
                    // Disable current file in menu.
                    if (menufilename === wpviewer.current_file) {
                        // this item is disabled.
                        disabledval = 'true';
                    }
                    $menuitem = wpviewer.make_menu_item(menuname, menufilename, disabledval);
                    $menufrag.append($menuitem);
                });
                // Add final menu and show it.
                $('#file-menu-items').append($menufrag);
                $('#file-menu').fadeIn();
            } else {
                // Re-mark current file (disable current file in menu)
                $.each($('.vertical-menu-link'), function () {
                    // get name from this link.
                    menuname = $(this).children().text();
                    // fix onclick for view_file(), by disabling links on all other files.
                    wpviewer.enable_link(this, (menuname !== wpviewer.current_name));
                });
            }
        }

    },
    make_menu_item : function (menuname, menufilename, disabledval) {
        /*  Create a menu item/link from a name, filename, and enabled/disabled value.
            Returns a jQuery object containing the element.
            Arguments:
                menuname      : short file name (file.py)
                menufilename  : relative file name (/static/blah/file.py)
                disabledval   : 'true', or 'false' (sent to onclick: view_file() )
                                must be string value. default is 'false'
        */
        if (!disabledval) { disabledval = 'false'; }

        var $menulink = $(document.createElement('a'));
        // Silence jslint.
        var jslink = 'javascript';
        jslink = jslink + ':';

        $menulink.attr('href', jslink + ' void(0);');
        $menulink.attr('class', 'vertical-menu-link');
        // add child list element/name
        var $menuitem = $(document.createElement('li'));
        $menuitem.addClass('vertical-menu-item');
        if (disabledval === 'true') {
            $menuitem.addClass('vertical-menu-item-disabled');
        }
        // add child span element/name
        var $menutxt = $(document.createElement('span'));
        $menutxt.addClass('vertical-menu-text');
        // make text a child of list, which is a child of the link.
        $menutxt.text(menuname);
        $menuitem.append($menutxt);
        $menulink.append($menuitem);

        $menulink.attr(
            'onclick',
            jslink + ' wpviewer.view_file(\'' + menufilename + '\', ' + disabledval + ');'
        );

        // needs disabled class?
        if (disabledval === 'true') {
            $menulink.addClass('vertical-menu-item-disabled');
        }
        // return menu link item
        return $menulink;
    },

    set_current_file : function (filename) {
        if (filename) {
            if (filename[0] === '/') {
                wpviewer.current_file = filename;
            } else {
                wpviewer.current_file = '/' + filename;
            }
            // set shortname for file.
            var nameparts = wpviewer.current_file.split('/');
            wpviewer.current_name = nameparts[nameparts.length - 1];

        }
    },

    setup_ace: function (initial_filename) {
        wp_content = ace.edit('file-content');
        // Disabled ace scrolling to new selected text.
        wp_content.$blockScrolling = Infinity;

        // highlight style
        wp_content.setTheme(wptools.default_ace_theme || 'ace/theme/solarized_dark');
        // various settings for ace
        wp_content.setHighlightActiveLine(true);
        wp_content.setAnimatedScroll(true);
        wp_content.setFontSize(14);
        // ensure read-only access to content
        wp_content.setReadOnly(true);
        wp_modelist = ace.require('ace/ext/modelist');

        // if an initial filename was passed, set the mode for it.
        if (initial_filename) {
            // get file mode for ace based on filename.
            var ace_mode = wp_modelist.getModeForPath(initial_filename);
            if (ace_mode) {
                wp_content.getSession().setMode(ace_mode.mode);
            }
        }
    },

    update_loading_msg: function (message) {
        $('#floater-msg').html(message);
        var $floater = $('#floater');
        wptools.center($floater);
        var scrollpos = $(this).scrollTop();
        $floater.css({'top': (scrollpos + 200) + 'px'});
        $floater.fadeIn();
    },

    view_file: function (filename, cancel) {
        if (cancel || !filename) {
            // view_file() links can be disabled by doing: javascript: view_file(..filename, true)
            return false;
        }

        // JSON data to send...
        var filedata = { file: filename };

        // change the loading message for proper file name.
        var displayname = wpviewer.current_file || filename;
        wpviewer.update_loading_msg('<span>Loading file: ' + displayname + '...</span>');

        $('#file-info').fadeOut();
        /*jslint unparam:true*/
        $.ajax({
            type: 'post',
            contentType: 'application/json',
            url: '/view/file/',
            data: JSON.stringify(filedata),
            dataType: 'json',
            status: {
                404: function () { console.log('PAGE NOT FOUND!'); },
                500: function () { console.log('A major error occurred.'); }
            }
        })
            .fail(function (xhr, status, error) {
                var msg = error.message || 'The error was unknown.';
                console.log('failure: ' + status + '\n    ' + msg);
                $('#file-content-box').html('<span class=\'B\'>Sorry, an unhandled error occurred. ' + msg + '</span>');
            })
            .done(function (data, status, xhr) {

                // handle errors...
                if (status === 'error') {
                    $('#file-content-box').html('<span class=\'B\'>Sorry, either that file doesn\'t exist, or there was an error processing it.</span>');
                    console.log('wp-error response: ' + xhr.responseText);
                } else {
                    // Data okay to use, send it to the file loader.
                    wpviewer.load_file_data(xhr);
                }
                // done loading success or error
                $('#floater').fadeOut();
            });
    }
};
