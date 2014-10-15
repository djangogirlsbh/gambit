# ==============================================================================
# users.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django import forms

# ------------------------------------------------------------------------------
# Forms
# ------------------------------------------------------------------------------

class UploadPGNGameForm(forms.Form):
    """
    User uploading a PGN file.
    """
    pgn_file = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'class': 'form-control'}))
    users_game = forms.BooleanField(required=False)

class ImportChesscomForm(forms.Form):
    """
    Import Chess.com games for a user.
    """
    chesscom_username = forms.CharField(max_length=64,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Username'}))
    users_game = forms.BooleanField(required=False)
