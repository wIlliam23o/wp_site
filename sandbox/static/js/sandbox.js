var sandbox = { // eslint-disable-line no-unused-vars
    get_json: function (url, cb) {
        /* Just a snippet really, an example of using $.ajax and deferreds. */
        return $.ajax({'url': url})
            .done(function (data, txtstatus, xhr) { // eslint-disable-line no-unused-vars
                if (cb !== 'undefined' && cb !== null) {
                    cb(data);
                }
            })
            .fail(function (xhr, txtstatus, errorthrown) {
                console.log('Error retrieving JSON: ' + txtstatus);
                console.log(errorthrown);
            });
    },
};
