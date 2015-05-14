![welborn prod.](http://welbornprod.com/static/images/welbornprod-logo.png)

[Django] site for [welbornprod.com]...


It features a blog app I made to suit my needs, projects, web applications,
and miscellaneous scripts that I've written for one reason or another.
It's a mixture of [Python]/[Django], HTML/Templates, JavaScript, and SASS/CSS.
It uses a Postgres backend to handle all the storage.


I wasn't able to find many pre-made 'apps' to do exactly what I wanted,
so I ended up making my own. I admit that most of these apps couldn't be
'dropped into' another project without bringing the 'wp_main' app and some
other stuff with it, but in the beginning of this project I wasn't sure about
what a 'good django project' looked like.

The 'searcher' app is now decoupled from the models. It depends on
`INSTALLED_APPS`, and looks for a `search.py` within the apps. As long as the
"must-have" functions are implemented in `search.py` the app's models can
be searched.

The 'downloads' depends on the other apps, as it updates the 'download_count'
on many objects.

The 'viewer' will show extra info depending on whether a file is related to a
project or not, and also updates the 'view_count' on objects that have one.


There is one section where things are much more isolated. The 'apps' are meant
to stand alone. They still depend on the home/main.html template,
but work with their own set of tools and models.


The 'wp_main' app holds many utilities that are used throughout the other apps.
It's sort of the 'global settings/tools' app. Many things in 'home' could be,
and probably need to be, moved there. Maybe some day soon I'll do that.


At the least, maybe someone could take inspiration from the apps, or modify them
to work with their setup.


-----------------------

_*Language/Libraries*_:
-----------------------

**Python 3+**

  <small>...this isn't 100% Python 2 compatible anymore.</small>

**Django 1.5+**

  <small>...awesome web framework that made this possible</small>

**Django Debug Toolbar**

  <small>...for very useful debugging info in the browser.</small>

**Django User Agents**

  <small>...using it for browser/mobile detection right now. </small>

  <small>...currently looking for alternative methods.</small>

**Django Extensions**

  <small>...several extra tools to use with Django.

**Pygments**

  <small>...used for source code highlighting</small>

**Twython**

  <small>...uses the Twitter API to retrieve latest tweets.</small>


**...various other standard libraries.**



_*Note:*_
---------
The site is live, if you'd like to see what I have so far you can do so here:

[welbornprod.com]

It's running on an [Apache] server, hosted by [WebFaction].

[![I Love Open Source](http://www.iloveopensource.io/images/logo-lightbg.png)](http://www.iloveopensource.io/projects/53e6d33587659fce660044fe)

   [welbornprod.com]: http://welbornprod.com "welbornprod.com"
   [welbornprod.info]: http://welbornprod.info "welbornprod.info"
   [Django]: http://djangoproject.com
   [Apache]: http://httpd.apache.org
   [Python]: http://python.org
   [WebFaction]: http://webfaction.com
