function change_content(s) {
    /* Change ace editor content, move selection to start. */
    wp_content.setValue(s);
    wp_content.selection.selectFileStart();
}

// handles valid responses from viewer.views.view_loader() and .ajax_contents()
function load_file_data (xhrdata) {
    var file_info = JSON.parse(xhrdata.responseText);
    
    // Server-side error.
    if (file_info.status == 'error') {
        var errmessage = file_info.message;
        if (errmessage) {
            $("#file-content-box").html("<span>" + errmessage + "</span>");
        } else {
            $("#file-content-box").html("<span>Sorry, an unknown error occurred.</span>");
        }
        return;
    }

    // Content
    if (file_info.file_content) {
        // Load content into ace editor...
        change_content(file_info.file_content);
        // Set Language
        var ace_mode = wp_modelist.getModeForPath(file_info.static_path);
        wp_content.getSession().setMode(ace_mode.mode);
        $('#file-content').fadeIn();

    } 
    else {
        $("#file-content-box").html("<span>Sorry, no content in this file...</span>");
        return;
    }

    /* Header for projects ...pythons None equates to null in JS. */
    if (file_info.project_alias !== null && file_info.project_name !== null) {
        $("#project-title-name").html(file_info.project_name);
        $("#project-link").click( function () { wptools.navigateto("/projects/" + file_info.project_alias); });
        if (file_info.project_alias) { $("#project-info").fadeIn(); }
    // Header for miscobj.
    } else if (file_info.misc_alias !== null && file_info.misc_name !== null) {
        $("#project-title-name").html(file_info.misc_name);
        $("#project-link").click( function () { wptools.navigateto("/misc/" + file_info.misc_alias); });
        if (file_info.misc_alias) { $("#project-info").fadeIn(); }
    }
    // File info
    if (file_info.file_short && file_info.static_path) {
        $("#viewer-filename").html(file_info.file_short);
        $("#file-link").click( function () { wptools.navigateto("/dl/" + file_info.static_path ); });
        if (file_info.file_short) { $("#file-info").fadeIn(); }
    }
        
    // Menu builder
    var menu_items = file_info.menu_items;
    if (menu_items) {
        var menu_length = menu_items.length;
        var existing_items = $(".vertical-menu-item");
        var existing_length = existing_items.length;
        // only build the menu once...
        if (existing_length === 0 && menu_length > 0 ) {
            $.each(menu_items, function () {
                $("#file-menu-items").append("<a href='javascript: view_file(\"" + this[0].replace(/[ ]/g, '/') + "\");'>" +
                                             "<li class='vertical-menu-item'>" + 
                                             "<span class='vertical-menu-text'>" + this[1] + "</span></li></a>");
            });
            $("#file-menu").fadeIn();
        }
    }
        
}

// setup initial ace editor
function setup_ace (initial_filename) {
    wp_content = ace.edit('file-content');
    // highlight style
    wp_content.setTheme('ace/theme/solarized_dark');
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
}

// update floater message and size/position
function update_loading_msg (message) {
    $("#loading-msg").html(message);
    wptools.center_element("#floater");
    var floater = $("#floater");
    var scrollpos = $(this).scrollTop();
    floater.css({'top': (scrollpos + 200) + 'px'});
    
    $("#floater").fadeIn();
}

function view_file (filename) {
	var filedata = { file: filename };

	// change the loading message for proper file name.
	update_loading_msg("<span>Loading file: " + filename + "...</span>");

	//$("#project-info").fadeOut();
	$("#file-info").fadeOut();
	
	$.ajax({
		type: "post",
		contentType: "application/json",
		url: "/view/file/",
		data: JSON.stringify(filedata),
		dataType: "json",
		failure: function (xhr, status, errorthrown) {
			console.log("failure: " + status);
		},
		complete: function (xhr, status) {
						
			// handle errors...
			if (status == 'error') {
				$("#file-content-box").html("<span class='B'>Sorry, either that file doesn't exist, or there was an error processing it.</span>");
				console.log('wp-error response: ' + xhr.responseText);
			} 
			else {
				// Data okay to use, send it to the file loader.
				load_file_data(xhr);
			}
			// done loading success or error
			$("#floater").fadeOut();
		},
		status: {
			404: function () { console.log('PAGE NOT FOUND!'); },
			500: function () { console.log('A major error occurred.'); }
		}
	});

}



