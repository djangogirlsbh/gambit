# ==============================================================================
# chesscom_crawler.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from time import sleep
from urllib2 import urlopen

from archive_page import ArchivePage
from chess_com.mapper.eco_mapper import ECOMapper
from chess_com.models.models import ChessGame
from chess_com.parser.pgn_parser import PGNParser

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
                * eco_details
        """
        result = []

        last_game_id = self.get_last_game_id(user)
        crawl_url = self.make_crawl_url(self.GAME_TYPES['live'])
        page = ArchivePage(crawl_url)

        while page.page_opened:
            game_ids = page.get_game_ids()

            for game_id in game_ids:
                if game_id <= last_game_id:
                    page.page_opened = False
                    break

                game = self.extract_pgn_data(game_id)
                result.append(game)

                job.games_processed += 1
                job.save()

                sleep(2)

            page.next_page()

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
            * eco_details

        Arguments:
            game_id<int> -- Chess.com game ID.

        Returns:
            Dictionary of parsed PGN data.
        """
        result = {}

        pgn_data = self.download_pgn(game_id)

        if pgn_data:
            parser = PGNParser(pgn_data)
            mapper = ECOMapper()

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
            result['eco_details'] = mapper.get_eco_details(pgn_data)

        return result

    def download_pgn(self, game_id):
        """
        Attempt to download the PGN contents of a Chess.com game.

        Arguments:
            game_id<int> -- Chess.com game ID.

        Returns:
            The contents of the PGN file as a string, or None if file could not
            be read.
        """
        result = None

        try:
            url = self.BASE_DOWNLOAD_PATH % str(game_id)
            result = urlopen(url).read()
        except Exception as error:
            message = 'UserGamesCrawler.download_pgn() unable to download ' \
                'PGN contents. Details: %s' % error
            print ' '.join(['[WARN]', message])

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

    def get_last_game_id(self, user):
        """
        Finds the Chess.com ID of the the most recently played game currently
        available in the database.

        Arguments:
            user<User> -- User to find most recent game's ID for.

        Returns:
            Chess.com game ID or -1 if none was found.
        """
        result = -1

        try:
            users_games = ChessGame.objects.filter(uploaded_by=user,
                users_game=True,
                chesscom_id__isnull=False)
            games_ordered = users_games.order_by('chesscom_id')

            if games_ordered:
                most_recent_game = games_ordered[len(games_ordered) - 1]
                result = most_recent_game.chesscom_id
        except Exception as error:
            message = 'UserGamesCrawler.get_last_game_id() could not find ' \
                'user\'s most recently played game. Details: %s' % error
            print ' '.join(['[WARN]', message])

        return result
