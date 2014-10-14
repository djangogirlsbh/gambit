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

from django.contrib.auth.models import User

from models import ChessGame
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

    def get_live_games(self, user, job):
        """
        Gets the live games played by the user.

        Arguments:
            user<User>     -- User searching for games.
            job<ImportJob> -- Holds the status of the current import job.

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
                * chesscom_id
        """
        result = []

        recent_game_id = self.get_recent_game_id(user)
        crawl_url = self.make_crawl_url(self.GAME_TYPES['live'])
        page = urlopen(crawl_url).read()
        page_number = 1

        while page:
            game_ids = map(int, self.get_game_ids(page))

            for game_id in game_ids:
                if game_id <= recent_game_id:
                    page = None
                    break

                game = self.extract_pgn_data(game_id)
                result.append(game)

                job.games_processed += 1
                job.save()
                sleep(2)

            page = self.next_page(page, page_number) if page else None
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
                * chesscom_id

        Arguments:
            game_id<int> -- Chess.com game ID.

        Returns:
            Dictionary of parsed PGN data or None if not found.
        """
        result = {}

        url = self.BASE_DOWNLOAD_PATH % str(game_id)
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
        result['chesscom_id'] = game_id

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

        try:
            soup = BeautifulSoup(html)
            anchors = soup.find_all('a',
                href=re.compile('page=%d$' % (page_number + 1)))
            url = self.BASE_URL + anchors[0]['href']
            result = urlopen(url).read()
        except Exception:
            pass

        return result

    def make_crawl_url(self, game_type):
        """
        Creates a starting crawling URL for the given game type.

        Arguments:
            game_type<string> -- Value of the Chess.com game type.

        Returns:
            Absolute URL to the starting crawl point.
        """
        params = self.BASE_ARCHIVE_PARAMS % (game_type, self.username)
        url = self.BASE_ARCHIVE_URL + params
        return url

    def get_recent_game_id(self, user):
        """
        Finds the Chess.com ID of the the most recently played game currently
        available in the database.

        Arguments:
            user<User> -- User to find most recent game's ID for.

        Returns:
            Chess.com game ID or -1 if none was found.
        """
        result = -1

        users_games = ChessGame.objects.filter(uploaded_by=user,
            chesscom_id__isnull=False)
        games_ordered = users_games.order_by('chesscom_id')

        if games_ordered:
            most_recent_game = games_ordered[len(games_ordered) - 1]
            result = most_recent_game.chesscom_id

        return result
