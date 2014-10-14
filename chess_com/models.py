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

    uploaded_by = models.ForeignKey(User)
    users_game = models.BooleanField()

    raw_pgn = models.CharField(max_length=10000)
