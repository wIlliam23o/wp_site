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
    version: '0.0.1',
    username: null,
    userinfo: null,
    avatar_url: null,
    name: null,
    repos: 0,
    forks: 0,
    stars: 0,

    build: function (username, cbsuccess, cberror) {
        github_badge.get_info(
            username,
            function success() {
                var forkplural = github_badge.forks === 1 ? '' : 's',
                    starplural = github_badge.stars === 1 ? '' : 's';

                var lblrepos = github_badge.repos === 1 ? 'repo' : 'repos',
                    lblforks = 'fork' + forkplural,
                    lblforktimes = 'time' + forkplural,
                    lblstars = 'star' + starplural,
                    lblstartimes = 'time' + starplural;

                cbsuccess($([
                    '<div id="github-badge">',
                    '  <div id="github-badge-branding">',
                    '    <a href="https://github.com" target="_blank">',
                    '      <div class="github-badge-branding-label">github.com</div>',
                    '    </a>',
                    '  </div>',
                    '  <div id="github-badge-main">',
                    '    <div class="github-badge-header">',
                    '      <a href="https://github.com/' + github_badge.username + '">',
                    '        <img class="github-badge-avatar" src="' + github_badge.avatar_url + '">',
                    '      </a>',
                    '      <a href="https://github.com/' + github_badge.username + '">',
                    '        <div class="github-badge-username"><strong>' + github_badge.username + '</strong></div>',
                    '      </a>',
                    '      <div class="github-badge-name">' + github_badge.name + '</div>',
                    '    </div>',
                    '    <div class="github-badge-info">',
                    '      <div class="github-badge-info-item" title="' + github_badge.name + ' has created ' + github_badge.repos + ' ' + lblrepos + '.">',
                    '        <span class="github-badge-info-value">' + github_badge.repos + '</span>',
                    '        <span class="github-badge-info-label">' + lblrepos + '</span>',
                    '      </div>',
                    '      <div class="github-badge-info-div"></div>',
                    '      <div class="github-badge-info-item" title="' + github_badge.name + ' has been forked ' + github_badge.forks + ' ' + lblforktimes + '.">',
                    '        <span class="github-badge-info-value">' + github_badge.forks + '</span>',
                    '        <span class="github-badge-info-label">' + lblforks + '</span>',
                    '      </div>',
                    '      <div class="github-badge-info-div"></div>',
                    '      <div class="github-badge-info-item" title="' + github_badge.name + ' has been starred ' + github_badge.stars + ' ' + lblstartimes + '.">',
                    '        <span class="github-badge-info-value">' + github_badge.stars + '</span>',
                    '        <span class="github-badge-info-label">' + lblstars + '</span>',
                    '      </div>',
                    '    </div>',
                    '  </div>',
                    '</div>'
                ].join('\n')));
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
        github_badge.name = data.name || 'unknown';
        github_badge.avatar_url = data.avatar_url || null;
        github_badge.repos = data.public_repos || 0;

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
    }
};
