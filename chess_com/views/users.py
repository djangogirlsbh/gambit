# ==============================================================================
# users.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from thread import start_new_thread

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.template import RequestContext

from chess_com.analysis.games_analyzer import GamesAnalyzer
from chess_com.crawler.chesscom_crawler import UserGamesCrawler
from chess_com.forms.users import ImportChesscomForm, UploadPGNGameForm
from chess_com.mapper.eco_mapper import ECOMapper
from chess_com.models.models import ChessGame, ImportJob
from chess_com.parser.pgn_parser import PGNParser

# ------------------------------------------------------------------------------
# Views
# ------------------------------------------------------------------------------

@login_required
def import_games(request):
    context = {}

    # POST request
    if request.method == 'POST':

        # User uploading single PGN game
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

        # User importing Chess.com games
        elif 'import' in request.POST:
            form = ImportChesscomForm(request.POST)
            if form.is_valid():
                chesscom_username = form.cleaned_data['chesscom_username']
                users_game = form.cleaned_data['users_game']
                handle_imports(request.user, chesscom_username, users_game)
                return redirect('games')
            else:
                context['import_form'] = form

    # Non-POST request
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
        chesscom_id__isnull=False).order_by('-chesscom_id')
    stats = None

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

        analyzer = GamesAnalyzer(games, player, 50)
        stats = analyzer.get_stats()

        context['overall_played'] = stats['overall']['total']
        context['overall_won'] = stats['overall']['won']
        context['overall_lost'] = stats['overall']['lost']
        context['overall_drawn'] = stats['overall']['drawn']
        context['white_played'] = stats['white']['total']
        context['white_won'] = stats['white']['won']
        context['white_lost'] = stats['white']['lost']
        context['white_drawn'] = stats['white']['drawn']
        context['black_played'] = stats['black']['total']
        context['black_won'] = stats['black']['won']
        context['black_lost'] = stats['black']['lost']
        context['black_drawn'] = stats['black']['drawn']
        context['rating_by_game'] = stats['ratings']
        context['rating_labels'] = stats['rating_labels']
        context['white_games'] = stats['white_openings']
        context['black_games'] = stats['black_openings']

    return render(request,
        'users/track.html',
        context,
        context_instance=RequestContext(request))

@login_required
def games(request):
    """
    Gets all the users games.
    """
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
    thread_args = (user, username, users_games)
    start_new_thread(import_chesscom_games, thread_args)

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
    live_games = []

    try:
        games = crawler.get_live_games(user, job)
        live_games.extend(games)
    except Exception as error:
        message = 'import_chesscom_games() had trouble getting live games. ' \
            'Details: %s' % error
        print ' '.join(['[ERROR]', message])

    for pgn_game in live_games:
        try:
            game = ChessGame.objects.create(white_name=pgn_game['white_name'],
                black_name=pgn_game['black_name'],
                white_rating=pgn_game['white_rating'],
                black_rating=pgn_game['black_rating'],
                game_result=pgn_game['game_result'],
                time_control=pgn_game['time_control'],
                total_moves=pgn_game['total_moves'],
                date_played=pgn_game['date_played'],
                eco_details=pgn_game['eco_details'],
                uploaded_by=user,
                users_game=users_games,
                chesscom_id=pgn_game['chesscom_id'],
                raw_pgn=pgn_game['raw_pgn'])
            game.save()
        except Exception as error:
            message = 'import_chesscom_games() could not save game. ' \
                'Details: %s' % error
            print ' '.join(['[ERROR]', message])

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
        pgn_data = pgn_file.read()
        parser = PGNParser(pgn_data)
        mapper = ECOMapper()

        white_name = parser.extract_white_name()
        black_name = parser.extract_black_name()
        white_rating = parser.extract_white_rating()
        black_rating = parser.extract_black_rating()
        game_result = parser.extract_game_result()
        time_control = parser.extract_time_control()
        total_moves = parser.extract_total_moves()
        date_played = parser.extract_date_played()
        eco_details = mapper.get_eco_details(pgn_data)

        try:
            game = ChessGame.objects.create(white_name=white_name,
                black_name=black_name,
                white_rating=white_rating,
                black_rating=black_rating,
                game_result=game_result,
                time_control=time_control,
                total_moves=total_moves,
                date_played=date_played,
                eco_details=eco_details,
                uploaded_by=user,
                users_game=users_game,
                raw_pgn=pgn_data)
            game.save()
        except Exception as error:
            result = 'Sorry, unable to parse PGN file.'

    return result
