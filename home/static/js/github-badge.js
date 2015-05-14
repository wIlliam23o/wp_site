/*  Welborn Productions - Github Badge

    My old third-party github badge stopped working. It wouldn't display
    proper information for organizations, and any server errors left me with
    a big ugly iframe with the word 'ERROR' on it.

    So I made this github badge myself, drawing inspiration from the old one.
    It parses the api info client side and builds the html needed to display
    a badge. Because of the github api design, it uses two ajax calls to gather
    the required info.

    Example use:
        <!-- Include all necessary files. -->
        <link type='text/css' rel='stylesheet' href='github-badge.css'>
        <script type='text/javascript' src='github-badge.js'></script>

        <!-- Create a div to put the badge in. -->
        <div id="github-badge-wrapper">
        </div>

        <!-- Fill it with the badge on document.ready -->
        <script type='text/javascript'>
            $(document).ready(function () {
                github_badge.build_badge(
                    'myusername',
                    function success(div) {
                        // div is an element containing the badge.
                        $('#github-badge-wrapper').html(div);
                    },
                    function error(error_message) {
                        // Somewhere down the line it failed, so don't show the div.
                        console.log('Cannot build github badge: ' + error_message);
                        $('#github-badge-wrapper').css({display: 'none'});
                    }
                );
            });
        </script>
*/
'use strict';
var github_badge = {
    version: '0.0.2',
    // Github user info.
    username: null,
    userinfo: null,
    avatar_url: null,
    name: null,
    repos: 0,
    forks: 0,
    stars: 0,
    followers: 0,

    build: function (username, cbsuccess, cberror) {
        github_badge.get_info(
            username,
            function success() {
                // Build the final html, send it to the callback.
                cbsuccess($(github_badge.render_template(github_badge)));
            },
            cberror
        );

    },

    get_info: function (username, cbsuccess, cberror) {
        github_badge.username = username;

        /*jslint unparam:true*/
        $.ajax('https://api.github.com/users/' + username, {
            dataType: 'json',
            error: function (jqr, status) {
                cberror(status);
            },
            success: function (data) {
                github_badge.userinfo = data;
                github_badge.parse_info(data, cbsuccess, cberror);
            }

        });
    },

    parse_info: function (data, cbsuccess, cberror) {
        var force_int = function force_int(value, fallback) {
            /* Parse a string as an integer. Use the default on failure. */
            var val = parseInt(value, 10);
            return val.toString() === 'NaN' ? (fallback || 0) : val;
        };

        github_badge.name = data.name || 'unknown';
        github_badge.avatar_url = data.avatar_url || null;

        github_badge.repos = force_int(data.public_repos, 0);
        github_badge.followers = force_int(data.followers, 0);

        /*jslint unparam:true*/
        $.ajax('https://api.github.com/users/' + github_badge.username + '/repos', {
            dataType: 'json',
            error: function (jqr, status) {
                cberror(status);
            },
            success: function (data) {
                var repolen = data.length,
                    i = 0,
                    own_repos = 0,
                    stars = 0,
                    forks = 0;
                var repo;

                if (!repolen) {
                    return;
                }
                for (i; i < repolen; i++) {
                    repo = data[i];
                    if ((repo.fork !== undefined) && (!repo.fork)) {
                        own_repos++;
                    }
                    if (repo.stargazers_count) {
                        stars += repo.stargazers_count;
                    }
                    if (repo.forks_count) {
                        forks += repo.forks_count;
                    }
                }
                github_badge.repos = own_repos;
                github_badge.stars = stars;
                github_badge.forks = forks;
                cbsuccess();
            }
        });
    },

    render_template: function (obj) {
        /*  Return an element containing the formatted badge.
            Expects an object with these attributes:
                forks, stars, followers, repos, username, name, avatar_url
        */
        var forkplural = obj.forks === 1 ? '' : 's',
            starplural = obj.stars === 1 ? '' : 's',
            followersplural = obj.followers === 1 ? '' : 's';

        var lblrepos = obj.repos === 1 ? 'repo' : 'repos',
            lblforks = 'fork' + forkplural,
            lblforktimes = 'time' + forkplural,
            lblstars = 'star' + starplural,
            lblstartimes = 'time' + starplural,
            lblfollowers = 'follower' + followersplural;

        var humanize_count = function (val) {
            /*  Use a 'k' to symbolize thousands.
                If the number is less then 1000, just return it.
            */
            if (val < 1000) {
                return val.toString();
            }
            return (val / 1000).toFixed(1) + 'k';
        };

        return [
            '<div id="github-badge">',
            '  <div id="github-badge-branding">',
            '    <a href="https://github.com" target="_blank">',
            '      <div class="github-badge-branding-label">github.com</div>',
            '    </a>',
            '  </div>',
            '  <div id="github-badge-main">',
            // Username, avatar, name.
            '    <div class="github-badge-header">',
            '      <a href="https://github.com/' + obj.username + '">',
            '        <img class="github-badge-avatar" src="' + obj.avatar_url + '">',
            '      </a>',
            '      <a href="https://github.com/' + obj.username + '">',
            '        <div class="github-badge-username"><strong>' + obj.username + '</strong></div>',
            '      </a>',
            '      <div class="github-badge-name">' + obj.name + '</div>',
            '    </div>',
            // Counts
            '    <ul class="github-badge-info">',
            '      <li class="github-badge-info-left">',
            '        <div class="github-badge-info-item" title="' + obj.name + ' has created ' + obj.repos + ' ' + lblrepos + '.">',
            '          <span class="github-badge-info-value">' + humanize_count(obj.repos) + '</span>',
            '          <span class="github-badge-info-label">' + lblrepos + '</span>',
            '        </div>',
            '        <div class="github-badge-info-item" title="' + obj.name + ' has been forked ' + obj.forks + ' ' + lblforktimes + '.">',
            '          <span class="github-badge-info-value">' + humanize_count(obj.forks) + '</span>',
            '          <span class="github-badge-info-label">' + lblforks + '</span>',
            '        </div>',
            '      </li>',
            '      <li class="github-badge-info-right">',
            '        <div class="github-badge-info-item" title="' + obj.name + ' has been starred ' + obj.stars + ' ' + lblstartimes + '.">',
            '          <span class="github-badge-info-value">' + humanize_count(obj.stars) + '</span>',
            '          <span class="github-badge-info-label">' + lblstars + '</span>',
            '        </div>',
            '        <div class="github-badge-info-item" title="' + obj.name + ' has ' + obj.followers + ' ' + lblfollowers + '.">',
            '          <span class="github-badge-info-value">' + humanize_count(obj.followers) + '</span>',
            '          <span class="github-badge-info-label">' + lblfollowers + '</span>',
            '      </li>',
            '    </ul>',
            '  </div>',
            '</div>'
        ].join('\n');
    },

    url_info: function (options) {
        /*global window, document*/
        /*  Gathers info and parameters from a url (window.location.href).

            Options:
                {
                    url:         Url to work with.
                                 Default: window.location.href
                    unescape:    Unescape url-escaped stuff.
                                 Default: true
                    convert_num: Convert integer-like arguments to integers.
                                 Default: true
                }
        */
        var url_search_arr,
            option_key,
            i,
            urlObj,
            get_param,
            key,
            val,
            url_query,
            url_get_params = {},
            a = document.createElement('a'),
            default_options = {
                'url': window.location.href,
                'unescape': true,
                'convert_num': true
            };

        if (typeof options !== "object") {
            options = default_options;
        } else {
            for (option_key in default_options) {
                if (default_options.hasOwnProperty(option_key)) {
                    if (options[option_key] === undefined) {
                        options[option_key] = default_options[option_key];
                    }
                }
            }
        }

        a.href = options.url;
        url_query = a.search.substring(1);
        url_search_arr = url_query.split('&');

        if (url_search_arr[0].length > 1) {
            for (i = 0; i < url_search_arr.length; i += 1) {
                get_param = url_search_arr[i].split("=");

                if (options.unescape) {
                    key = decodeURI(get_param[0]);
                    val = decodeURI(get_param[1]);
                } else {
                    key = get_param[0];
                    val = get_param[1];
                }

                if (options.convert_num) {
                    if (val.match(/^\d+$/)) {
                        val = parseInt(val, 10);
                    } else if (val.match(/^\d+\.\d+$/)) {
                        val = parseFloat(val);
                    }
                }

                if (url_get_params[key] === undefined) {
                    url_get_params[key] = val;
                } else if (typeof url_get_params[key] === "string") {
                    url_get_params[key] = [url_get_params[key], val];
                } else {
                    url_get_params[key].push(val);
                }

                get_param = [];
            }
        }

        urlObj = {
            protocol: a.protocol,
            hostname: a.hostname,
            host: a.host,
            port: a.port,
            hash: a.hash.substr(1),
            pathname: a.pathname,
            search: a.search,
            parameters: url_get_params
        };

        return urlObj;
    }
};
