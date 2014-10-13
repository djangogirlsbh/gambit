# ==============================================================================
# views.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.template import RequestContext

from forms import RegistrationForm, SigninForm

# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------

def index(request):
    """
    Landing page.
    """
    return render(request,
        'landing/main.html',
        context_instance=RequestContext(request))

def about(request):
    """
    About page.
    """
    return render(request,
        'landing/about.html',
        context_instance=RequestContext(request))
 
def register(request):
    """
    Landing page.
    """
    context = {}

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            signup_user(username, password) 
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('main')
        else:
            context['registration_form'] = form
    else:
        context['registration_form'] = RegistrationForm()

    return render(request,
        'landing/register.html',
        context,
        context_instance=RequestContext(request))

def signin(request):
    """
    Attempts to sign in the user.
    """
    context = {}

    if request.method == 'POST':
        form = SigninForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('main')
            else:
                context['signin_error'] = 'Username/password is incorrect.'
                context['signin_form'] = form
        else:
            context['signin_form'] = form
    else:
        context['signin_form'] = SigninForm()

    return render(request,
        'landing/signin.html',
        context,
        context_instance=RequestContext(request))

def signout(request):
    """
    If the user is signed in, sign them out, else just redirect them to the main
    page (silly users).
    """
    logout(request)
    return redirect('main')

# ------------------------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------------------------

def signup_user(username, password):
    """
    Attempts to create a new user.

    Arguments:
        username<string> -- Username.
        password<string> -- Password.

    Returns:
        New User if successfully created, else None.
    """
    result = None

    try:
        result = User.objects.create_user(username, password=password)
    except Exception:
        pass

    return result
