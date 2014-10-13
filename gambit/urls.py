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
)
