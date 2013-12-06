var phonewords = {

    do_lookup: function () {
        if (phonewords.validate_submit()) {
            wptools.pre_ajax();
            $('#lookup-form').submit();
            return true;
        } else {
            return false;
        }
    },

    do_error : function (querytype, errmsg) {
        // Show error msg for query string.
        if (!querytype) { querytype = 'number'; }
        if (!errmsg) { errmsg = 'Must be a 7 digit number!'; }
        $('#floater-msg').text('Invalid ' + querytype + ' given!');
        $('#floater-msg').css({'color': '#A70000'});
        $('#floater-smalltext').text(errmsg);
        $('#floater').fadeIn();
        setTimeout(function () { $('#floater').fadeOut(); }, 2000);
        return false;
    },

    do_valid: function (querystr) {
        // Show wait msg for query string.
        $('#floater-msg').text('Generating results for: ' + querystr);
        $('#floater-msg').css({'color': '#4D4D4D'});
        $('#floater-smalltext').text('This may take 2-10 seconds');
        $('#floater').fadeIn();
        phonewords.waitmsg_anim();
        return true;
    },

    insert_result: function (combo, word) {
        var oldtext = $('#pw_results').val();
        $('#pw_results').val(oldtext + '\n' + combo + ' : ' + word);
    },

    is_number: function (s) {
        // Returns true for '777-7777', false for '77a-7777'
        if (s) {
            s = s.replace(/-/g, '');
        }
        return !isNaN(s);
    },

    validate_number: function (s) {
        // Validates number entry. Must be 7 digits.
        if (s) {
            return (s.length === 7);
        }
        return false;
    },

    validate_submit: function () {
        // Validate input based on type of input (word/number)
        var querystr = $('#query-box').val();
        var validnum = false;
        var lookupmode = 'number';
        var errmsg = 'Must be a 7 digit number!';
        if (querystr) {
            querystr = querystr.replace(/-/g, '');
            if (phonewords.is_number(querystr)) {
                validnum = phonewords.validate_number(querystr);
            } else {
                lookupmode = 'word';
                errmsg = 'Word must be 3 - 7 characters long!';
                validnum = phonewords.validate_word(querystr);
            }
        }
        // Show appropriate messages...
        if (validnum) {
            // Show wait msg.
            return phonewords.do_valid(querystr);
        } else {
            // Show error msg.
            return phonewords.do_error(lookupmode, errmsg);
        }
    },

    validate_word: function (s) {
        // Validate word entry (3 to 7 chars long)
        if (s) {
            return (s.length > 2 && s.length < 8);
        }
        return false;
    },

    waitmsg_anim : function () {
        // Recursive anim with 1 second delay...
        phonewords.waitmsg_change();
        setTimeout(function () { phonewords.waitmsg_anim(); }, 1000);
    },

    waitmsg_change : function () {
        var current = $('#floater-smalltext').text().replace(/\n/g, '');
        if (current && current.substr(-3) == '...') {
            // Back to original
            $('#floater-smalltext').text(current.substr(0, current.length - 3));
        } else {
            // just add a .
            $('#floater-smalltext').text(current + '.');
        }
    },

    waitmsg_fade : function () {
        // Not used.
        $('#floater-smalltext').fadeOut(1000).fadeIn(1000);
    }
};
