/* Welborn Productions - img - Javascript
    Provides tools on the client-side for the img app.
    -Christopher Welborn 2-2-15
*/

var imgtools = {
    do_upload : function () {
        var uploadform = $('#upload-form');
        if (wptools.is_hidden(uploadform)) {
            $(uploadform).slideDown();
        } else {
            wptools.pre_ajax();
            $('#upload-form').submit();
            $(uploadform).slideUp();
        }

    }
}
