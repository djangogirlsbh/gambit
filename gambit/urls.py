# ==============================================================================
# urls.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django.conf.urls import patterns, url

# ------------------------------------------------------------------------------
# Url routing
# ------------------------------------------------------------------------------

urlpatterns = patterns('',
    url(r'^$', 'chess_com.views.public.index', name='main'),
    url(r'^about', 'chess_com.views.public.about', name='about'),
    url(r'^register', 'chess_com.views.public.register', name='register'),
    url(r'^signin', 'chess_com.views.public.signin', name='signin'),
    url(r'^signout', 'chess_com.views.public.signout', name='signout'),

    url(r'^import', 'chess_com.views.users.import_games', name='import'),
    url(r'^games', 'chess_com.views.users.games', name='games'),
    url(r'^track', 'chess_com.views.users.track', name='track'),
)
