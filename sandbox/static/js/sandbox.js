var sandbox = {
    get_json: function (url, cb) {
        var response = null;
        return $.ajax({'url': url})
            .done(function (data, txtstatus, xhr) {
                if (cb !== 'undefined' && cb !== null) {
                    cb(data);
                }
            })
            .fail(function (xhr, txtstatus, errorthrown) {
                console.log('Error retrieving JSON: ' + txtstatus);
                console.log(errorthrown);
            })
    },

    get_json2: function (url) {
        return $.getJSON(url);
    },

    get_json3: function (url) {
        return $.get(url)
    }
};
