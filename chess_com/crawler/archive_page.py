# ==============================================================================
# archive_page.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from bs4 import BeautifulSoup
import re
from urllib2 import urlopen

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class ArchivePage(object):
    """
    Gets content for a Chess.com archive page, analyzes it's contents, finds
    specified elements.
    """

    def __init__(self, url):
        """
        Creates an analyzer for an archive page using the given URL. If the page
        is successfully opened, the page_opened flag is set.

        Arguments:
            url<string> -- Full URL to page.
        """
        self.BASE_PATH = 'http://www.chess.com/'

        self.page_opened = False
        self.current_page = 0

        self.url = url
        self.load_content()

    def load_content(self):
        """
        Attempts to load the contents of this object's page. If it succeeds, the
        page_opened flag is set, otherwise this silently fails.

        Note: This expects to be called upon object initialization (which will
        update the current page to 1) and on subsequent calls to next_page,
        which, if they succeed, increment the current page by one each time.
        """
        try:
            page_handler = urlopen(self.url)
            self.page_content = page_handler.read()
            self.page_opened = True
            self.current_page += 1
        except Exception as error:
            self.page_opened = False
            message = 'ArchivePage.load_content() unable to open %s for ' \
                'reading. Details: %s' % (self.url, error)
            print ' '.join(['[ERROR]', message])

    def get_game_ids(self):
        """
        Returns a list of game IDs found on the current archive page. If none
        are found or if the page is not opened, silently return an empty list.

        Returns:
            A list of game IDs as ints or an empty list if page is not open or
            there are no IDs.
        """
        result = []

        if not self.page_opened:
            message = 'ArchivePage.get_game_ids() called when page not open.'
            print ' '.join(['[WARN]', message])
            return result

        try:
            soup = BeautifulSoup(self.page_content)
            game_rows = soup.find_all('tr', id=re.compile('c14_row'))

            for game_row in game_rows:
                tds = game_row.find_all('td')
                link = tds[7].a['href']

                matches = re.search('id=(?P<game_id>\d+)', link)
                game_id = int(matches.group('game_id'))

                result.append(game_id)
        except Exception as error:
            message = 'ArchivePage.get_game_ids() unable to get game ID. ' \
                'Returning: %s. Details: %s.' % (result, error)
            print ' '.join(['[WARN]', message])

        return result

    def next_page(self):
        """
        Attempts to load the next archive page using the current one as a base.
        If there is no subsequent page or the current page is not open, this
        silently sets the page_opened flag to False.
        """
        if not self.page_opened:
            message = 'ArchivePage.next_page() called when page not open.'
            print ' '.join(['[WARN]', message])
            return

        try:
            soup = BeautifulSoup(self.page_content)
            anchors = soup.find_all('a',
                href=re.compile('page=%d$' % (self.current_page + 1)))

            path = anchors[0]['href']
            accurate_path = path[1:] if path[0] == '/' else path

            self.url = self.BASE_PATH + accurate_path
            self.load_content()
        except Exception as error:
            self.page_opened = False
            message = 'ArchivePage.next_page() unable to find next page. ' \
                'Details: %s' % error
            print ' '.join(['[INFO]', message])
