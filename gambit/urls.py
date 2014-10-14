# ==============================================================================
# urls.py
# ==============================================================================

# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from django.conf.urls import patterns, include, url

# ------------------------------------------------------------------------------
# Url routing
# ------------------------------------------------------------------------------

urlpatterns = patterns('',
    url(r'^$', 'chess_com.views.index', name='main'),
    url(r'^about', 'chess_com.views.about', name='about'),
    url(r'^register', 'chess_com.views.register', name='register'),
    url(r'^signin', 'chess_com.views.signin', name='signin'),
    url(r'^signout', 'chess_com.views.signout', name='signout'),

    url(r'^import', 'chess_com.views.import_games', name='import'),
    url(r'^games', 'chess_com.views.games', name='games'),
    url(r'^track', 'chess_com.views.track', name='track'),
)
