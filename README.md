![welborn prod.](http://welbornproductions.net/images/welbornprod-logo.png)

[Django] site for [welbornprod.com]...


Currently moving away from [Joomla], converting site to [Django] in the hopes of adding functionality and more control.

I am not a professional [Django] developer, nor am I really a web developer. Just a programmer trying to learn while
creating a web site that I can be proud of, and use the way I want to. This is the first [Django] project I have attempted,
so I'm sure there are things that I'm doing wrong. Still, I'm really enjoying it and I look forward to the things I can achieve with this setup.

[Joomla] is great for most people, especially people that don't want to learn to code. For me its a crutch, and I don't like
using crutches. I want to learn as much as I can about web development, [Django], and python at the same time. So while some of this might sound like a hate-filled rant, it's really just my own frustration shining through after dealing with [Joomla] for a year. It was built in a language I don't care to learn right now (php), which made it harder for me to tweak the core. It also had a lot of overhead and features that I didn't even use because I didn't need them. I'm a huge [Python] fan, so it makes sense that I would lean towards a web framework built around it.

------------------

_*Language/Libraries*_:
-----------------------

**Python 2.7.3+**

  <small>...just waiting for the right libraries before I switch to 3.</small>

**Django 1.5+**

  <small>...awesome web framework that made this possible</small>

**Django Debug Toolbar 0.9.4+**

  <small>...for very useful debugging info in the browser.</small>

**Django User Agents 0.2.1+**

  <small>...using it for browser/mobile detection right now. </small>

  <small>...currently looking for alternative methods.</small>

**Pygments 1.6+**

  <small>...used for source code highlighting</small>


...various other standard libraries.


_*Looks:*_
----------
I actually like the look of my old site, it was a template that I hacked and slashed to get what I wanted.
The problem was all the code files being scattered about, javascript all over the place that wasn't even used,
css settings overriding each other (template overrides joomla, joomla override gantry, etc.).
When I gathered all the css/js/other files that I actually needed and wanted, it turned out to be not that many.
Those few files had way too many selectors in them, that I wasn't even using and never plan to use.
Gantry was loading browser-specific css files, and then [Joomla] would load its own, and then my template.
That's just too much for me. 

So my first step was to condense everything I actually used into a reasonable length
of files.

The css menu, and menu-editing, from within [Joomla] was okay, but I really wanted more, and I'd rather edit an HTML file
than use [Joomla]'s menu editing system. So using [Django]'s template system, I was able to put my main background, main menu, and
footer in one place. Now I have a single base that I can edit to change the look of any page on my site. While I was at it, I decided
to use a fisheye javascript menu for the main menu, and an optional css dropdown on pages that need it.


_*Projects:*_
------------

The projects section was added first. Instead of writing an 'article' about my project (which always felt weird to me, 
calling it an 'article'.), I add the project with it's info (name, unique-alias, version, download_url, html_url, and more.) through
[Django] admin, and then I write the description page in HTML. My view locates each projects HTML description through it's property 
"html_url", and loads that html into the page. While it's loading the page it also looks for tags that I have embedded in the description
like "screenshots_code", "source_view", "download_code", "span class='highlight-embedded python'", and "pre class='python'".
Based on whether these tags exist, and whether or not the project has the info it's looking for, my views will start gathering information
about screen shots, source code, downloads, and such for each project. It will then generate the HTML needed to display this information
like I want it. So instead of writing a whole screenshots rotator box for each page, I just point the projects screenshots_dir to the
directory containing the images, and add "{{ screenshots_code }}" to the description where I would like the screenshots to be displayed.
This looks like a django-variable but it's not, I just got used to writing like that. To me it means "code will be injected here".

If the description has a pre tag with a valid pygments lexer name as the class, my view will call my highlighter module to highlight all
the code and return the highlighted code in HTML format. 

If the description has a span tag (really any tag I want to use) with the class "highlight-embedded \[language name\]", again the highlighter
is called and starts replacing that span tag with the highlighted content. This way, I can embed highlighted source code within a paragraph or
sentance.

These are both things I wanted to do with [Joomla], and maybe there was some add-on or [Apache] feature I could have used, but I'm just the type
of person that will write my own whenever I'm not happy with something, or don't feel like learning a whole new technology for one feature.

The download_code tag tells my view to look for the projects download_url. If its a directory it will use all files in that directory, and if
its a single file it will use that instead. This info is HTML formatted exactly how I want it, and then returned to the view to use. There
are a few other tags, they basically do the same thing. They gather info about the project, and return an HTML formatted string to display it.


_*Source/File Viewer:*_
-----------------------

The source viewer just loads the contents of any file, keeping the format of my site (logo, background, menu, etc.). If it's a source code file,
it will try to determine the pygments lexer needed (if any), and use it to highlight the file. If the file belongs to a project,
It will also look at the projects source_dir property and generate a css vertical menu of all files in that directory if any exist. 
This way, you can browse all source files within a project without leaving the source viewer. 


_*Downloads:*_
--------------

I use Google analytics, Adsense, and even my shared hosting provider's own analytics feature on my site, so tracking downloads isn't that hard.
My project views already increment the project's view_count whenever the page is loaded, but still,
I wanted to keep my own record of downloads. So each project has a download_count. To track the downloads, 
anytime I want to offer a download I make sure to start the url with "/dl/". This tells [Django] to send this file through my Download app. 
The download app doesn't do much, it just checks to see if the file being downloaded belongs to a project, and if it does it will increment 
the project's download_count property. Whether or not the file belongs to a project, the user is then redirected to the actual file for
download. A bit of security was added, if the url doesn't exist within my projects directory, we just won't use it. The function 
utilities.get_absolute_path() returns an empty string if it can't locate the file within the projects base dir. An empty string prompts all other
functions/code to abort gracefully with "This file doesn't exist.".
I don't want anyone downloading files from the root directory through some malformed url.


_*Blog:*_
---------

I wrote a basic blog app with tags, tag view, tag 'cloud', and pagination. The blog never has been the main feature on my site, so I didn't go too big with it. Just a place for my to jot down quick entries through django admin, or write up an HTML file (if the file is linked to an entry, its used instead of the TextField). It also has a 'projects' many-to-many field so I can link and projects the blog post might be related to. This is really for a future feature where a 'related projects' sidebar is automatically generated for the entry. I haven't started work on that yet. The blog listing and view has code-highlighting just like the projects section.

You can browse all posts containing a certain tag (tag-view, i'm calling it), or view all tags (with a link to the tag-view). If the post count, or tag-view results reaches my default 'max_items' setting, the pagination will kick in. A navigation bar is drawn by the template with first, last, prev, next links. These links pass GET arguments that tell my view where to start 'slicing' my posts with 'start_index' and 'max_items'. All of this works together so my view can generate a 'page' of posts/tag listings complete with navigation.


_*Search:*_
-----------

The search feature is very basic, but it works perfectly for what I need right now. I used an HTML form and POST arguments to pass a search query to my search view. It searches for a term (or space-separated terms) in the title, name, slug, alias, description, body, or externally linked html file. If anything is found, a results listing is built by my results.html template. If the results count reaches my max_items setting, the  pagination kicks in the same way as the blog pagination.


_*Sitemap/Robots.txt*_:
-----------------------

I looked into the django sitemaps library, but unfortunately it wasn't what I needed. Right now I'm hosting the same site at 2 different domains, so the sitemap that is generated by my view needs to reflect the domain name it's being accessed from. I built a very simple xml template that loops through a list of sitemap_url() items (a class I made especially for this feature) and builds the sitemap.xml. The list is built by my view_sitemap() view. It grabs the server name from the request, adds URLs for the main sections on my site, and then loops through my projects and blog entries building url links to them. On my test-server, a blank sitemap is served up because I don't need robots crawling a site that could possibly contain errors. On the production site, a nice and clean sitemap is served up for whatever domain it's being accessed through (welbornprod.com, or welbornprod.info).


The robots.txt is served up kinda the same way, except I only needed to return a one line HttpResponse() (if you don't count the \n char.). On the test-server, "Disallow: /" is returned in "text/plain" so any honest robots won't crawl it. On the production site, "Allow: /" is returned. I'm not sure if I even need that much, a blank one would probably suffice, this is one of those things I plan on looking in to. But for now, it works.


_*Future:*_
-----------

Now that I have a basic working site I plan on refining it and adding more features as I go. I'm looking forward to building web apps that actually 'do something', as opposed to just showing information about my projects and blog. 
 

_*Note:*_
---------
The site is live now, I'm hosting at 2 new domains while my old one is redirecting. Finally, the [Joomla] site is dead. If you'd like to see what I have so far you can do so here:

[welbornprod.com]

or

[welbornprod.info]

   [welbornprod.com]: http://welbornprod.com "welbornprod.com"
   [welbornprod.info]: http://welbornprod.info "welbornprod.info"
   [Joomla]: http://joomla.com
   [Django]: http://djangoproject.com
   [Apache]: http://httpd.apache.org
   [Python]: http://python.org
