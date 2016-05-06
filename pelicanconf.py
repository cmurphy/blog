#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Colleen Murphy'
COPYRIGHT_YEAR = 2015

SITENAME = u'Colleen\'s Blog'
SITEURL = ''
SITETITLE = u'Colleen Murphy'
SITESUBTITLE = u'Computerist'
SITEDESCRIIPTION = u'Resume and Blog of Colleen Murphy'

PATH = 'content'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
#LINKS = (('GitHub', 'http://github.com/cmurphy'),
#         ('LinkedIn', 'https://www.linkedin.com/in/colleen-murphy-23a65057'),
#         ('Stackalytics', 'http://stackalytics.com/report/users/krinkle'))

# Social widget
SOCIAL = (('twitter', 'https://twitter.com/pdx_krinkle'),
         ('github', 'http://github.com/cmurphy'),
         ('linkedin', 'https://www.linkedin.com/in/colleen-murphy-23a65057'),)

DEFAULT_PAGINATION = 10

MENUITEMS = (('blog', 'archives.html'),)

THEME = 'theme'

STATIC_PATHS = [ 'images', 'extra/favicon.ico' ]
EXTRA_PATH_METADATA = { 'extra/favicon.ico': { 'path': 'favicon.ico' } }

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
