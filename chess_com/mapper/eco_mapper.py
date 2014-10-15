# ==============================================================================
# eco_mapper.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import re

from eco_mapping import eco_mapping

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class ECOMapper(object):
    """
    Maps a game of chess in PGN format to it's ECO code.
    """

    def __init__(self):
        """
        Creates a mapper.
        """
        pass

    def get_eco_details(self, pgn_data):
        """
        Finds the full ECO details of a PGN game, it's ECO code and name.

        Arguments:
            pgn_data<string> -- Full PGN data.

        Returns:
            ECO code and name as a string.
        """
        result = eco_mapping['unknown']

        try:
            moves = self.get_moves(pgn_data)
            current_sequence = ''

            for move in moves:
                half_move = '.'.join([move[0], move[1]])
                current_sequence += half_move

                if current_sequence in eco_mapping:
                    result = eco_mapping[current_sequence]
                else:
                    break

                current_sequence = ' '.join([current_sequence, move[2]])

                if current_sequence in eco_mapping:
                    result = eco_mapping[current_sequence]
                else:
                    break

                current_sequence += ' '
        except:
            pass

        return result

    def get_moves(self, pgn_data):
        """
        Finds the moves made in the game.

        Arguments:
            pgn_data<string> -- Full PGN data.

        Returns:
            A list of tuples, where a tuple contains the move number, white's
            move, and black's move, e.g.: [(1, Nf3, d5)].
        """
        result = []

        try:
            exp = '(?P<num>\d+)\.(?P<white>\w+) (?P<black>[\d|\w|-]+)'
            result = re.findall(exp, pgn_data)

            if result[-1][2] == '1-0' or \
                    result[-1][2] == '0-1' or \
                    result[-1][2] == '1/2-1/2':
                last_item = result[-1]
                del result[-1]
                result.append((last_item[0], last_item[1], ''))
        except:
            pass

        return result
