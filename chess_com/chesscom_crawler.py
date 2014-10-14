# ==============================================================================
# chesscom_crawler.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from bs4 import BeautifulSoup
import re
from time import sleep
from urllib2 import urlopen

from pgn_parser import PGNParser

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class UserGamesCrawler(object):
    """
    Crawls and retrieves a Chess.com's user's games.
    """

    def __init__(self, username):
        """
        Creates a crawler capable of retrieving a Chess.com's user's games.

        Arguments:
            username<string> -- Chess.com username.
        """
        if not username:
            raise Exception('Username must not be empty.')

        self.BASE_URL = 'http://www.chess.com/'
        self.BASE_ARCHIVE_URL = self.BASE_URL + 'home/game_archive'
        self.BASE_ARCHIVE_PARAMS = '?sortby=&show=%s&member=%s'
        self.BASE_DOWNLOAD_PATH = self.BASE_URL + 'echess/download_pgn?lid=%s'
        self.GAME_TYPES = {
            'live': 'live',
            'turnbased': 'echess',
        }

        self.username = username

    def get_live_games(self):
        """
        Gets the live games played by the user.

        Returns:
            A list of dictionaries, each dictionary storing the PGN data from a
            game. Possible keys are:
                * white_name
                * black_name
                * white_rating
                * black_rating
                * game_result
                * time_control
                * total_moves
                * date_played
                * raw_pgn

        TODO: Given a User object, only look for games not already imported.
        """
        result = []

        params = self.BASE_ARCHIVE_PARAMS % (self.GAME_TYPES['live'],
            self.username)
        url = self.BASE_ARCHIVE_URL + params

        page, page_number = urlopen(url).read(), 1
        while page:
            game_ids = self.get_game_ids(page)
            for game_id in game_ids:
                game = self.extract_pgn_data(game_id)
                result.append(game)
                sleep(2)
            page = self.next_page(page, page_number)
            page_number += 1

        return result

    def get_turnbased_games(self):
        """
        """
        params = self.BASE_ARCHIVE_PARAMS % (self.GAME_TYPES['turnbased'],
            self.username)
        url = self.BASE_ARCHIVE_URL + params

    def get_game_ids(self, html):
        """
        Returns a list of the game IDs found on the details page.

        Arguments:
            html<string> -- Full HTML of a page.

        Returns:
            List of game IDs.
        """
        result = []

        soup = BeautifulSoup(html)
        game_rows = soup.find_all('tr', id=re.compile('c14_row'))

        for row in game_rows:
            tds = row.find_all('td')
            link = tds[7].a['href']
            matches = re.search('id=(?P<id>\d+)', link)
            result.append(matches.group('id'))

        return result

    def extract_pgn_data(self, game_id):
        """
        Attempts to download and parse PGN data. If found, attempts to parse it
        and return a dictionary of parsed data. Possible keys in the dictionary
        are:
                * white_name
                * black_name
                * white_rating
                * black_rating
                * game_result
                * time_control
                * total_moves
                * date_played
                * raw_pgn

        Arguments:
            game_id<string>   -- Chess.com game ID.

        Returns:
            Dictionary of parsed PGN data or None if not found.
        """
        result = {}

        url = self.BASE_DOWNLOAD_PATH % game_id
        print 'Download from: %s' % url
        pgn_data = urlopen(url).read()
        parser = PGNParser(pgn_data)

        result['white_name'] = parser.extract_white_name()
        result['black_name'] = parser.extract_black_name()
        result['white_rating'] = parser.extract_white_rating()
        result['black_rating'] = parser.extract_black_rating()
        result['game_result'] = parser.extract_game_result()
        result['time_control'] = parser.extract_time_control()
        result['total_moves'] = parser.extract_total_moves()
        result['date_played'] = parser.extract_date_played()
        result['raw_pgn'] = pgn_data

        return result

    def next_page(self, html, page_number):
        """
        Looks for the next page listing the user's games. If it finds it,
        returns the HTML contents, otherwise returns None.

        Arguments:
            html<string>     -- Full HTML on the current page.
            page_number<int> -- Page currently viewed.

        Returns:
            The HTML contents of the next page, or None if there is not one.
        """
        result = None
        expression = '<a href="(?P<path>.+page=%d)' % (page_number + 1)
        matches = re.search(expression, html)

        try:
            url = self.BASE_URL + matches.group('path')
            result = urlopen(url).read()
        except:
            pass

        return result
