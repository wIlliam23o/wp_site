![welborn prod.](http://welbornproductions.net/images/welbornprod-logo.png)

[Django] site for [welbornproductions.net]...

   [welbornproductions.net]: http://welbornproductions.net "Welborn Productions"

Currently moving away from [Joomla], converting site to [Django] in the hopes of adding functionality and more control.

I am not a professional [Django] developer, nor am I really a web developer. Just a programmer trying to learn while
creating a web site that I can be proud of, and use the way I want to. This is the first [Django] project I have attempted,
so I'm sure there are things that I'm doing wrong. Still, I'm really enjoying it and I look forward to the day when I can
go live with this thing.

[Joomla] is great for most people, especially people that don't want to learn to code. For me its a crutch, and I don't like
using crutches. I want to learn as much as I can about web development, [Django], and python at the same time. 

------------------

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


_*Content:*_
------------

Right now I have the projects section done. Instead of writing an 'article' about my project (which always felt weird to me, 
calling it an 'article'.), I add the project with it's info (name, unique-alias, version, download_url, html_url, and more.) through
[Django] admin, and then I write the description page in HTML. My view locates each projects HTML description through it's property 
"html_url", and loads that html into the page. While it's loading the page it also looks for tags that I have embedded in the description
like "screenshots_code", "source_view", "download_code", "span class='highlight-embedded python'", and "pre class='python'".
Based on whether these tags exist, and whether or not the project has the info it's looking for, my views will start gathering information
about screen shots, source code, downloads, and such for each project. It will then generate the HTML needed to display this information
like I want it. So instead of writing a whole screenshots rotator box for each article, I just point the projects screenshots_dir to the
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


_*Features:*_
-------------

There's also some other features that I might have done with [Joomla], but decided not to for the same reasons. This is the ability to view my project's
source code with syntax highlighting, or browse the source directory with highlighting of all files. Some browsers will highlight these files
for you, but some will not. So if the "source_view" tag is found in my project's description, my view will look at the projects source_file or 
source_dir property, and decide which one to use. It will then generate an HTML formatted link/listing for the project page that points to my 
next feature, the "Source Viewer". Actually, it's a file viewer, but it will automatically highlight any file using pygments if it can.


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


_*Future:*_
-----------

I'm about to start working on the Blog side of my site. I'm not much of a blogger, but every once in a while I like to give status updates about
me, or my projects, and I feel a blog is the right place to do it. I've been looking into [Django]'s blog packages, but I'm not seeing anything
that I want. Again, I'm the type that will write my own If I don't like something about the existing options out there. I'm not looking to make
a big open-source project for everyone to use. Just something for me, so I can get exactly what I want and nothing else. It'll have to have a
comment system of some sort, and ofcourse code highlighting (my work is already done there. see, [Django] is awesome.). The packages I'm seeing look
a lot like [Joomla]-addons, and I don't want to get into re-writing some huge blog package and still end up with a lot of extra stuff I don't even
use. The search isn't over yet though, I want to make sure there is absolutely nothing out there before I decide to write my own.


The search feature on my old site was always a little weird. It had all these [Joomla] examples indexed and even when I removed them from the index
they showed up in searches. I finally got them to stop showing up but I was too busy, or lazy, to delete them from the database. It bothers me. So
I'll have to write a decent search engine for my site. This won't be that bad actually, once I get the Blog section done I think the Search feature
will fall right into place. I'm not going for anything fancy anyway. 
 

_*Note:*_
---------
My public site is still using [Joomla], and I will not transfer the [Django] site over until it's stable.

My current host does several things that I disagree with like no mod_wsgi (and no way to get it),
no mod_python either (not that I wanted to go that route), and python 2.6 only. I currently use 2.7 and
3.3, and would rather continue to do so.

I've looked into other hosting options, and found one that works very well with projects like this.
I am currently testing with a local server and my new remote server, both [Apache] + mod_wsgi.

   [Joomla]: http://joomla.com
   [Django]: http://djangoproject.com
   [Apache]: http://httpd.apache.org/
