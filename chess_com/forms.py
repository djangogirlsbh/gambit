# ==============================================================================
# forms.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django import forms
from django.contrib.auth.models import User

# ------------------------------------------------------------------------------
# Forms
# ------------------------------------------------------------------------------

class SigninForm(forms.Form):
    """
    Sign in form.
    """ 
    username = forms.CharField(max_length=64,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Username'}))
    password = forms.CharField(max_length=64,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                      'placeholder': 'Password'}))

class RegistrationForm(forms.Form):
    """
    Registration form.
    """ 
    username = forms.CharField(max_length=64,
        widget=forms.TextInput(attrs={'class': 'form-control',
                                      'placeholder': 'Username'}))
    password = forms.CharField(max_length=64,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                      'placeholder': 'Password'}))
    password_confirm = forms.CharField(max_length=64,
        widget=forms.PasswordInput(attrs={'class': 'form-control',
                                      'placeholder': 'Confirm password'}))

    def clean(self):
        """
        Extra custom logic for ensuring user registration proceeds as it ought
        to.
        """
        cleaned_data = super(RegistrationForm, self).clean()

        username = cleaned_data.get('username')
        if username:
            if len(username) < 3:
                self._errors['username'] = 'Please use at least 3 letters.'
            else:
                try:
                    user = User.objects.get(username=username)
                    self._errors['username'] = 'This username is in use.'
                except:
                    pass

        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm:
            if len(password) < 6:
                self._errors['password'] = 'Please use at least 6 letters.'
            elif password and password_confirm and password != password_confirm:
                self._errors['password'] = 'Your passwords must match.'

        return cleaned_data

class UploadPGNGameForm(forms.Form):
    """
    User uploading a PGN file.
    """
    pgn_file = forms.FileField(widget=forms.ClearableFileInput(
        attrs={'class': 'form-control'}))
    users_game = forms.BooleanField(required=False)
