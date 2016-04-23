![welborn prod.](http://welbornprod.com/static/images/welbornprod-logo.png)

[Django] site for [welbornprod.com]...


It features a blog app I made to suit my needs, projects, web applications,
and miscellaneous scripts that I've written for one reason or another.
It's a mixture of [Python]/[Django], HTML/Templates, JavaScript, and SASS/CSS.
It uses a Postgres backend to handle all the storage.

## Django Apps:

All apps were created from scratch, because in the beginning I didn't see
many django apps to suit my specific needs.

#### Apps:

The `apps` are web-based applications, and are meant to stand alone.
They still depend on the home/main.html template, but work with their own
set of tools and models.

##### Apps/Paste:

The `paste` app is a paste-bin that uses Ace Editor to provide
syntax-highlighted viewing/editing. Pastes expire after a day, unless they
are 'on-hold'. They can have parents/replies, which are displayed in the
listing and on the paste's view.
Pastes can be private <small>(unlisted)</small> or public.

##### Apps/PhoneWords:

The `phonewords` app will find common english words that can be formed with
a U.S. phone number, or the reverse (words to phone numbers).

#### Blogger:

The `blogger` app is a basic blog app, with pagination and a brief index page.
This has nothing to do with the more popular django app named 'blogger'.

#### Downloads:

The `downloads` app tracks the download count for any file, as long as it
is linked to `/dl/file`. Right now it is coupled with several other apps,
to update the `download_count` on the Project/Misc/etc. objects themselves,
instead of just the file name.

#### Home:

The `home` app provides a landing page for the site, with featured projects,
blog posts, and web apps.

#### Img:

The `img` app provides an image uploader/viewer. Only admins can upload an
image.

#### Misc:

The `misc` app provides a list of 'Misc. Objects', which are miscellaneous
scripts/modules that are too small to warrant a full 'Project' page.

#### Projects:

The `projects` app provides a list of 'Projects', which are various programs
that I've written over the years.

#### Searcher:

The `searcher` app allows various models to be searched. It gathers the
objects and buids a `WpResult` based on their attributes defined in
`app/search.py`.
It depends on `INSTALLED_APPS`, and looks for a `search.py` within the apps.
As long as the *must-have* functions are implemented in `search.py` the app's
models can be searched.

#### Stats:

The `stats` app provides view/download counts for the various models found
in the other apps. It currently provides the counts for apps, pastes,
blog posts, file trackers, images, misc objects, and projects.

#### Viewer:

The `viewer` app will display a syntax-highlighted file, and will show extra
information if the file is related to a Project/Misc. It also updates the
`view_count` on the Project/Misc/etc. objects for files that are related to
these objects.

#### Wp_Main:

The `wp_main` app holds many utilities that are used throughout the other apps.
Common http responses, response filters, html methods, server-side
highlighting methods, tweet tools, and various other utility methods are found
here. The main SASS imports are also in `wp_main`.


_____________________________________________________________________________

## Language/Libraries:

**Python 3+**

  <small>...this isn't 100% Python 2 compatible anymore.</small>

**Django 1.8.3+** - (`django`)

  <small>...awesome web framework that made this possible</small>

**Django Debug Toolbar** - (`django-debug-toolbar`)

  <small>...for very useful debugging info in the browser.</small>

**Django Extensions** - (`django-extensions`)

  <small>...several extra tools to use with Django.

**Django Solo** - (`django-solo`)

  <small>...provides singleton models, for home config.</small>

**Django User Agents** - (`django-user-agents`)

  <small>...using it for browser/mobile detection right now. </small>

  <small>...currently looking for alternative methods.</small>

**Pygments** - (`pygments`)

  <small>...used for source code highlighting</small>

**Twython** - (`twython`)

  <small>...uses the Twitter API to retrieve latest tweets.</small>

There is a working `requirements.txt` that lists all the python dependencies
more precisely.

## Notes:

The site is live, if you'd like to see what I have so far you can do so here:

[welbornprod.com]

It's running on an [Apache] server, hosted by [WebFaction].

_____________________________________________________________________________

[![I Love Open Source](http://www.iloveopensource.io/images/logo-lightbg.png)](http://www.iloveopensource.io/projects/53e6d33587659fce660044fe)

   [welbornprod.com]: https://welbornprod.com "welbornprod.com"
   [welbornprod.info]: https://welbornprod.info "welbornprod.info"
   [Django]: http://djangoproject.com
   [Apache]: http://httpd.apache.org
   [Python]: http://python.org
   [WebFaction]: http://webfaction.com
