# ==============================================================================
# games_analyzer.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------------

class GamesAnalyzer(object):
    """
    Takes a list of games and performs analysis on them.
    """

    def __init__(self, games, username, max_labels=10, max_openings=3):
        """
        Creates an analyzer for list of games taking into account the focus
        player.

        Arguments:
            games<[ChessGame]> -- List of chess games.
            username<string>   -- Name of player to focus on stats for.
            max_labels<int>    -- Maximum number of labels to show on ratings
                                  graph.
            max_openings<int>  -- Maximum number of openings to get stats on
                                  per color.
        """
        self.TOTAL = 'total'
        self.WON = 'won'
        self.LOST = 'lost'
        self.DRAWN = 'drawn'

        self.OVERALL = 'overall'
        self.WHITE = 'white'
        self.BLACK = 'black'

        self.OPENING_POSTFIX = '_openings'
        self.WHITE_OPENINGS = ''.join([self.WHITE, self.OPENING_POSTFIX])
        self.BLACK_OPENINGS = ''.join([self.BLACK, self.OPENING_POSTFIX])

        self.RATINGS = 'ratings'
        self.RATING_LABELS = 'rating_labels'

        self.games = games
        self.username = username
        self.max_labels = max_labels
        self.max_openings = max_openings

    def get_stats(self):
        """
        Creates a dictionary housing extensive statistics on the games given for
        user. This includes:
            * Overall wins, losses, draws
            * Wins, losses, draws as white
            * Wins, losses, draws as black
            * Ratings over time and labels for these games
            * Most commonly used openings and wins, losses, draws for each color

        Returns:
            See the stats dictionary for details.
        """
        stats = {
            self.OVERALL: {self.TOTAL: 0,
                           self.WON: 0,
                           self.LOST: 0,
                           self.DRAWN: 0},
            self.WHITE: {self.TOTAL: 0,
                           self.WON: 0,
                           self.LOST: 0,
                           self.DRAWN: 0},
            self.BLACK: {self.TOTAL: 0,
                           self.WON: 0,
                           self.LOST: 0,
                           self.DRAWN: 0},
            self.WHITE_OPENINGS: None,
            self.BLACK_OPENINGS: None,
            self.RATINGS: [],
            self.RATING_LABELS: [],
        }

        white_games, black_games = {}, {}

        for game in self.games:
            color = self.get_color(game)
            result = self.get_result(game, color)
            rating = self.get_rating(game, color)
            label = str(game.date_played)

            self.set_results(stats, color, result)
            self.set_ratings(stats, rating, label)

            openings = white_games if color == self.WHITE else black_games
            self.set_openings(openings, game.eco_details, result)

        self.scratch_labels(stats[self.RATING_LABELS])
        white_openings = self.scratch_openings(white_games)
        black_openings = self.scratch_openings(black_games)
        stats[self.WHITE_OPENINGS] = white_openings
        stats[self.BLACK_OPENINGS] = black_openings

        stats[self.RATINGS].reverse()
        stats[self.RATING_LABELS].reverse()

        return stats 

    def set_results(self, stats, color, result):
        """
        Increase the wins, losses, and draws for the given color and totals for
        both colors

        Arguments:
            stats<{}>      -- Main stats dict, see get_stats() for details.
            color<string>  -- Color the player was playing during the game.
            result<string> -- Result of the game.
        """
        stats[self.OVERALL][self.TOTAL] += 1
        stats[self.OVERALL][result] += 1
        stats[color][self.TOTAL] += 1
        stats[color][result] += 1

    def set_ratings(self, stats, rating, label):
        """
        Adds the rating for this game to the list of ratings and sets its label
        for the graph.

        Arguments:
            stats<{}>     -- Main stats dict, see get_stats() for details.
            rating<int>   -- Player's rating for the current game.
            lable<string> -- Label for the game as it shows on the graph.
        """
        stats[self.RATINGS].append(int(rating))
        stats[self.RATING_LABELS].append(label)

    def set_openings(self, openings, eco_details, result):
        """
        Increase the wins, losses, and draws for the given opening for the
        color, or initialize the stats if this opening has not been encountered.

        Arguments:
            openings<{}>        -- Openings stats dictionary.
            eco_details<string> -- Current game.
            result<string>      -- Result of the game.
        """
        if eco_details in openings:
            openings[eco_details][self.TOTAL] += 1
            openings[eco_details][result] += 1
        else:
            openings[eco_details] = {
                self.TOTAL: 1,
                self.WON: 0,
                self.LOST: 0,
                self.DRAWN: 0,
            }
            openings[eco_details][result] += 1

    def scratch_labels(self, labels):
        """
        Remove labels evenly until they number of actual labels is less than the
        maximum.

        Arguments:
            labels<[string]> -- List of labels for graph.
        """
        current_labels = len(labels)

        n = 2
        while current_labels > self.max_labels:
            for index, label in enumerate(labels):
                if index % n != 0:
                    labels[index] = ''

            current_labels = len(filter(lambda x: x != '', labels))
            n *= 2

    def scratch_openings(self, openings):
        """
        Sort the openings by most games played and keep only the maximum allowed.

        Arguments:
            openings<{}> -- Dictionary of openings for some color.

        Returns:
            A list containing the dictionaries elements sorted by most played.
        """
        sorted_openings = sorted(openings.items(),
            key=lambda x: x[1][self.TOTAL],
            reverse=True)[:self.max_openings]
        return sorted_openings

    def get_color(self, game):
        """
        Get the player's color for the game.

        Arguments:
            game<ChessGame> -- Game to find player's color for.

        Returns:
            Either 'black' or 'white'. Will throw an exception if player was not
            found in the game.
        """
        result = None

        if game.white_name == self.username:
            result = self.WHITE
        elif game.black_name == self.username:
            result = self.BLACK
        else:
            raise Exception('Unable to find user in game.')

        return result

    def get_result(self, game, color):
        """
        Checks if the player won, lost, or drew the game.

        Arguments:
            game<ChessGame> -- Game to check result on.
            color<string>   -- Color of player to check result.

        Returns:
            One of 'won', 'lost', or 'drawn'.
        """
        result = None

        if game.game_result == '1-0':
            result = self.WON if color == self.WHITE else self.LOST
        elif game.game_result == '0-1':
            result = self.WON if color == self.BLACK else self.LOST
        else:
            result = self.DRAWN

        return result

    def get_rating(self, game, color):
        """
        Get the rating of the player by color.

        Arguments:
            game<ChessGame> -- Game to check result on.
            color<string>   -- Color of player to check result.

        Returns:
            The rating as an int of the player identified by color.
        """
        return game.white_rating if color == self.WHITE else game.black_rating
