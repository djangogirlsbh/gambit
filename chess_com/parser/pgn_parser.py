# ==============================================================================
# pgn_parser.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from datetime import date
import re

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class PGNParser(object):
    """
    Parses useful information from PGN files.
    """

    def __init__(self, pgn_contents):
        """
        Creates a PGN parser for a PGN file.

        Arguments:
            pgn_contents<string> -- PGN file contents.
        """
        self.content = pgn_contents

    def extract_white_name(self):
        """
        Finds white player's name.

        Returns:
            White player's name or None if it could not be found.
        """
        return self.get_string_tag('White')

    def extract_black_name(self):
        """
        Finds black player's name.

        Returns:
            Black player's name or None if it could not be found.
        """
        return self.get_string_tag('Black')

    def extract_white_rating(self):
        """
        Finds white player's rating.

        Returns:
            White player's rating or None if it could not be found.
        """
        return self.get_int_tag('WhiteElo')

    def extract_black_rating(self):
        """
        Finds black player's rating.

        Returns:
            Black player's rating or None if it could not be found.
        """
        return self.get_int_tag('BlackElo')

    def extract_game_result(self):
        """
        Finds the result of the game.

        Returns:
            Result of the game or None if it could not be found.
        """
        return self.get_string_tag('Result')

    def extract_time_control(self):
        """
        Finds the time control of the game.

        Returns:
            Time control of the game or None if it could not be found.
        """
        return self.get_string_tag('TimeControl')

    def extract_total_moves(self):
        """
        Find the total number of moves made in the game.
        Note: Ugly implementation.

        Returns:
            Total moves made in game.
        """
        result = None

        try:
            candidates = re.findall('\d+\.', self.content)
            last = candidates[-1]
            result = int(last[:-1])
        except:
            pass

        return result

    def extract_date_played(self):
        """
        Finds the date the game was played.

        Returns:
            A date object of the date the game was played, or None if it could
            not be found.
        """
        result = None

        try:
            date_string = self.get_string_tag('Date')
            expression = '(?P<year>\d+)\.(?P<month>\d+)\.(?P<day>\d+)'
            matches = re.search(expression, date_string)

            year = int(matches.group('year'))
            month = int(matches.group('month'))
            day = int(matches.group('day'))

            result = date(year, month, day)
        except:
            pass

        return result

    def extract_game_site(self):
        """
        Finds the site the game was played at.

        Returns:
            Site the game was played at, or None if it could not be found.
        """
        return self.get_string_tag('Site')

    def get_string_tag(self, tag):
        """
        PGN files have tags of the form:
            [<TAG> "<VALUE>"]

        This extracts the value for the given tag if it exists, otherwise None.

        Arguments:
            tag<string> -- The tag to look for.

        Returns:
            The value of the tag as a string if it exists, else None.
        """
        result = None

        try:
            expression = '\[%s "(?P<value>.+)"\]' % tag
            matches = re.search(expression, self.content)
            result = matches.group('value')
        except:
            pass

        return result

    def get_int_tag(self, tag):
        """
        PGN files have tags of the form:
            [<TAG> "<VALUE>"]

        This extracts the value for the given tag if it exists, otherwise None.

        Arguments:
            tag<string> -- The tag to look for.

        Returns:
            The value of the tag as an int if it exists, else None.
        """
        result = None

        try:
            result = int(self.get_string_tag(tag))
        except:
            pass

        return result
