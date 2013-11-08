from django.conf.urls import patterns, url
urlpatterns = patterns('neemi.views',
    url(r'^authenticate/(?P<service>[a-z]+)/$', 'authenticate_redirect',
        name='authenticate_redirect'),
    url(r'^singly_authorize/callback/$', 'singly_authorize_callback',
        name='singly_authorize_callback'),
    url(r'^plaid_authorize/callback/$', 'plaid_authorize_callback',
        name='plaid_authorize_callback'),
    url(r'^dropbox_authorize/callback/$', 'dropbox_authorize_callback',
        name='dropbox_authorize_callback'),
    url(r'^twitter_authorize/callback/$', 'twitter_authorize_callback',
        name='twitter_authorize_callback'),
    url(r'^linkedin_authorize/callback/$', 'linkedin_authorize_callback',
        name='linkedin_authorize_callback'),
    url(r'^foursquare_authorize/callback/$', 'foursquare_authorize_callback',
        name='foursquare_authorize_callback'),
    url(r'^facebook_authorize/callback/$', 'facebook_authorize_callback',
        name='facebook_authorize_callback'),
    url(r'^google_authorize/callback/$', 'google_authorize_callback',
        name='google_authorize_callback'),
    url(r'^login/$', 'neemi_login',
        name='neemi_login'),
    url(r'^delete_user/$', 'neemi_delete_user',
        name='neemi_delete_user'),
    url(r'^logout/$', 'neemi_logout',
        name='neemi_logout')
)

urlpatterns += patterns('neemi.search',
    url(r'^keyword_search/(?P<service>[a-z]+)/$', 'simple_keyword_search',
        name='simple_keyword_search')
 )

urlpatterns += patterns('neemi.data',
    url(r'^get_user_data/(?P<service>[a-z]+)/$', 'get_user_data',
        name='get_user_data')
)
