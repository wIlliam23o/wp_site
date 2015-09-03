""" Welborn Productions - Searcher - Objects.
    ...Provides a WpResult object for searcher and searchable apps.
    -Christopher Welborn 9-2-15
"""


class WpResult(object):

    """ Holds search result information. """

    def __init__(self, title='', link='', desc='', posted='', restype=''):
        # Title for the link that is generated in this result.
        self.title = title
        # Link href for this result.
        self.link = link
        # Small description for this result.
        self.description = desc
        # Publish date for this result.
        self.posted = posted
        # Type of result (project, blog post, misc, etc.)
        if not restype:
            self.restype = 'Unknown'
        else:
            self.restype = str(restype).title()

    def __str__(self):
        """ String version, for debugging. """
        fmtlines = [
            'WpResult:',
            '  restype: {}',
            '  title  : {}',
            '  link   : {}',
            '  desc   : {}',
            '  posted : {}'
        ]
        return '\n'.join(fmtlines).format(
            self.restype,
            self.title,
            self.link,
            self.description,
            self.posted)

    def __repr__(self):
        """ repr() for debugging. """
        fmt = 'WpResult(\'{t}\', \'{l}\', \'{d}\', \'{p})\', \'{r}\')'
        return fmt.format(
            t=self.title,
            l=self.link,
            d=self.description,
            p=self.posted,
            r=self.restype)

    @classmethod
    def from_dict(cls, d):
        """ Return a new WpResult from a dict.
            Raises KeyError on missing keys/args.
        """
        return cls(
            title=d['title'],
            link=d['link'],
            desc=d['desc'],
            posted=d['posted'],
            restype=d['restype']
        )
