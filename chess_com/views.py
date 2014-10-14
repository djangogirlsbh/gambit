# ==============================================================================
# views.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.template import RequestContext

from chesscom_crawler import UserGamesCrawler
from forms import ImportChesscomForm, RegistrationForm, SigninForm, \
    UploadPGNGameForm
from models import ChessGame, ImportJob
from pgn_parser import PGNParser

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

@login_required
def import_games(request):
    context = {}

    if request.method == 'POST':
        if 'upload' in request.POST:
            form = UploadPGNGameForm(request.POST, request.FILES)
            if form.is_valid():
                pgn_file = request.FILES['pgn_file']
                users_game = form.cleaned_data['users_game']
                error = upload_pgn(pgn_file, request.user, users_game)
                if not error:
                    return redirect('games')
                else:
                    context['upload_error'] = error
                    context['upload_form'] = form
            else:
                context['upload_form'] = form
        elif 'import' in request.POST:
            form = ImportChesscomForm(request.POST)
            if form.is_valid():
                chesscom_username = form.cleaned_data['chesscom_username']
                users_game = form.cleaned_data['users_game']
                error = import_chesscom_games(request.user,
                    chesscom_username,
                    users_game)
                if not error:
                    return redirect('games')
                else:
                    context['import_error'] = error
                    context['import_form'] = form
            else:
                context['import_form'] = form
    else:
        context['upload_form'] = UploadPGNGameForm()
        context['import_form'] = ImportChesscomForm()

    return render(request,
        'users/import.html',
        context,
        context_instance=RequestContext(request))

@login_required
def track(request):
    return render(request,
        'users/track.html',
        context_instance=RequestContext(request))

@login_required
def games(request):
    context = {}

    users_games = ChessGame.objects.filter(uploaded_by=request.user)
    context['users_games'] = users_games

    return render(request,
        'users/games.html',
        context,
        context_instance=RequestContext(request))

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

def import_chesscom_games(user, username, users_games):
    """
    Attempts to crawl Chess.com in search of a user's games, then imports them.

    Arguments:
        user<User>        -- User requesting the import.
        username<string>  -- Username of Chess.com member.
        users_games<bool> -- True if the username provided is the user.
    """
    result = None

    # TODO: The following forks and executes asynchronously, while we return to
    # caller. Crawler receives an ImportJob object and updates the object during
    # it's progress. The view for games sends the template an import job if one
    # exists for the user, so they can see the progress. Meanwhile, after we
    # fork and return, the caller returns the user to the games page, where they
    # will see the job's progress. This could be a good candidate for Redis.
    crawler = UserGamesCrawler(username)
    job = ImportJob.objects.create(user=user, games_processed=0)
    live_games = crawler.get_live_games(user, job)

    try:
        for pgn_game in live_games:
            game = ChessGame.objects.create(white_name=pgn_game['white_name'],
                black_name=pgn_game['black_name'],
                white_rating=pgn_game['white_rating'],
                black_rating=pgn_game['black_rating'],
                game_result=pgn_game['game_result'],
                time_control=pgn_game['time_control'],
                total_moves=pgn_game['total_moves'],
                date_played=pgn_game['date_played'],
                uploaded_by=user,
                users_game=users_games,
                chesscom_id=pgn_game['chesscom_id'],
                raw_pgn=pgn_game['raw_pgn'])
            game.save()
    except Exception as error:
        result = 'Unable to import games. Details: %s' % error

    job.delete()

    return result

def upload_pgn(pgn_file, user, users_game):
    """
    Uploads a PGN file for the user.

    Arguments:
        pgn_file<UploadedFile> -- Raw PGN file.
        user<User>             -- User uploading the file.
        users_game<bool>       -- True if this is the user's game.

    Returns:
        An error string if the game could not be uploaded, else None.
    """
    result = None

    if pgn_file.size > 10000:
        result = 'Please only submit files less than 10,000 bytes.'
    else:
        parser = PGNParser(pgn_file.read())

        white_name = parser.extract_white_name()
        black_name = parser.extract_black_name()
        white_rating = parser.extract_white_rating()
        black_rating = parser.extract_black_rating()
        game_result = parser.extract_game_result()
        time_control = parser.extract_time_control()
        total_moves = parser.extract_total_moves()
        date_played = parser.extract_date_played()

        try:
            game = ChessGame.objects.create(white_name=white_name,
                black_name=black_name,
                white_rating=white_rating,
                black_rating=black_rating,
                game_result=game_result,
                time_control=time_control,
                total_moves=total_moves,
                date_played=date_played,
                uploaded_by=user,
                users_game=users_game,
                raw_pgn=pgn_file)
            game.save()
        except Exception as error:
            result = 'Unable to parse PGN file.'

    return result
