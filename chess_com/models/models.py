# ==============================================================================
# models.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django.contrib.auth.models import User
from django.db import models

# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class ChessGame(models.Model):
    """
    Stores a chess game with full, raw PGN notation and separate metadata.
    """
    white_name = models.CharField(max_length=128)
    white_rating = models.IntegerField(blank=True)
    black_name = models.CharField(max_length=128)
    black_rating = models.IntegerField(blank=True)

    game_result = models.CharField(max_length=32)
    time_control = models.CharField(max_length=32, blank=True)
    total_moves = models.IntegerField()
    date_played = models.DateField()
    eco_details = models.CharField(max_length=128, blank=True)

    uploaded_by = models.ForeignKey(User)
    users_game = models.BooleanField()
    chesscom_id = models.BigIntegerField(blank=True, null=True)

    raw_pgn = models.CharField(max_length=10000)

    class Meta:
        app_label= 'chess_com'

class ImportJob(models.Model):
    """
    Represents a currently executing job to import a user's Chess.com games.
    This is deleted upon job completion.
    """
    user = models.ForeignKey(User)
    games_processed = models.IntegerField()

    class Meta:
        app_label= 'chess_com'
