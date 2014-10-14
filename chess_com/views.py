# ==============================================================================
# views.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import thread

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
                error = handle_imports(request.user,
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
    context = {}

    games = ChessGame.objects.filter(uploaded_by=request.user,
        users_game=True,
        chesscom_id__isnull=False)

    if len(games) < 2:
        context['stats_error'] = 'Cannot create stats with less than two games.'
    else:
        player = None
        game_1, game_2 = games[0], games[1]

        if game_1.white_name == game_2.white_name:
            player = game_1.white_name
        elif game_1.white_name == game_2.black_name:
            player = game_1.white_name
        elif game_1.black_name == game_2.black_name:
            player = game_1.black_name

        overall_won, overall_lost, overall_drawn = 0, 0, 0
        white_played, white_won, white_lost, white_drawn = 0, 0, 0, 0
        black_played, black_won, black_lost, black_drawn = 0, 0, 0, 0
        ratings, rating_labels = [], []

        num_labels = 10 if len(games) > 20 else 5
        skipped_labels = len(games) / num_labels

        for count, game in enumerate(games):
            if count % skipped_labels == 0:
                rating_labels.append(str(game.date_played))
            else:
                rating_labels.append('')

            if game.white_name == player:
                if game.game_result == '1-0':
                    overall_won += 1
                    white_won += 1
                elif game.game_result == '0-1':
                    overall_lost += 1
                    white_lost += 1
                else:
                    overall_drawn += 1
                    white_drawn += 1
                white_played += 1
                ratings.append(int(game.white_rating))
            else:
                if game.game_result == '1-0':
                    overall_lost += 1
                    black_lost += 1
                elif game.game_result == '0-1':
                    overall_won += 1
                    black_won += 1
                else:
                    overall_drawn += 1
                    black_drawn += 1
                black_played += 1
                ratings.append(int(game.black_rating))

        ratings.reverse()
        rating_labels.reverse()

        context['overall_played'] = len(games)
        context['overall_won'] = overall_won
        context['overall_lost'] = overall_lost
        context['overall_drawn'] = overall_drawn
        context['white_played'] = white_played
        context['white_won'] = white_won
        context['white_lost'] = white_lost
        context['white_drawn'] = white_drawn
        context['black_played'] = black_played
        context['black_won'] = black_won
        context['black_lost'] = black_lost
        context['black_drawn'] = black_drawn
        context['rating_by_game'] = ratings
        context['rating_labels'] = rating_labels

    return render(request,
        'users/track.html',
        context,
        context_instance=RequestContext(request))

@login_required
def games(request):
    context = {}

    chesscom_games = ChessGame.objects.filter(uploaded_by=request.user,
        users_game=True,
        chesscom_id__isnull=False)
    users_games = ChessGame.objects.filter(uploaded_by=request.user,
        users_game=True,
        chesscom_id__isnull=True)
    other_games = ChessGame.objects.filter(uploaded_by=request.user,
        users_game=False)

    users_jobs = ImportJob.objects.filter(user=request.user)

    context['chesscom_games'] = chesscom_games
    context['users_games'] = users_games
    context['other_games'] = other_games
    context['users_jobs'] = users_jobs

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

def handle_imports(user, username, users_games):
    """
    Begins crawling Chess.com for the user's games -- but in the background. A
    job is created to track this progress so the user can view the job status
    from the games page.

    Arguments:
        user<User>        -- User requesting the import.
        username<string>  -- Username of Chess.com member.
        users_games<bool> -- True if the username provided is the user.
    """
    thread.start_new_thread(import_chesscom_games,
        (user, username, users_games))

def import_chesscom_games(user, username, users_games):
    """
    Attempts to crawl Chess.com in search of a user's games, then imports them.

    Arguments:
        user<User>        -- User requesting the import.
        username<string>  -- Username of Chess.com member.
        users_games<bool> -- True if the username provided is the user.
    """
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
