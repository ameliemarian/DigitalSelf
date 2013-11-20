
import requests
import oauth2 as oauth
import urllib
import urlparse

# Python wrapper for the foursquare v2 API
# https://github.com/mLewisLogic/foursquare
# pip install foursquare
import foursquare

try:
    import simplejson as json
except ImportError:
    import json

try:
    import httplib2
except ImportError:
    pass

from webapp import settings
from webapp.settings import FOURSQUARE_CLIENT_ID, FOURSQUARE_CLIENT_SECRET, FOURSQUARE_REDIRECT_URI


auth_url          = 'https://foursquare.com/oauth2/authenticate'
access_token_url  = 'https://foursquare.com/oauth2/access_token'



class Foursquare(object):

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri


    def build_url(self, request={}):
        data = {
            'client_id': self.client_id,
            'response_type': u'code',
            'redirect_uri': self.redirect_uri,
        }
        #url = '{auth_url}?{params}'.format(auth_url=auth_url, params=urllib.urlencode(data))
        url = '%s?client_id=%s&response_type=code&redirect_uri=%s' % (auth_url, self.client_id, self.redirect_uri)
        return url


    def authorize(self, oauth_code=None):
        print "authorize... "

        # Build the token uri to request
        url = '%s?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=%s&code=%s' % (access_token_url, self.client_id, self.client_secret, self.redirect_uri, oauth_code)

        try:
            # Get the response from the token uri and attempt to parse
            #h = httplib2.Http(disable_ssl_certificate_validation=True)
            h = httplib2.Http(ca_certs='/usr/local/lib/python2.7/dist-packages/httplib2/cacerts.txt')
            response, content = h.request(url, 'GET')

            try:
                data = json.loads(content)
            except ValueError, e:
                raise ApiError(e)

            if response.status == 200:
                #access_token = dict(urlparse.parse_qsl(content))
                access_token = data.get('access_token')
                return access_token

        except httplib2.HttpLib2Error, e:
            errmsg = u'Error connecting with foursquare API: {0}'.format(e)
            raise ApiError(e)


    def create_client_withoutWrapper(self, access_token=None):
        print "create client..."
        consumer = oauth.Consumer(self.client_id, self.client_secret)    
        token = oauth.Token(access_token)
        client = oauth.Client(consumer, token)
        return client     


    def create_client(self, access_token=None):
        print "create client..."
        client = foursquare.Foursquare(access_token=access_token)
        return client 


class FoursquareHelper(object):

    @classmethod
    def get_authorize_url(self, service=None):
        print "get authorized url..."
        api = Foursquare(FOURSQUARE_CLIENT_ID, FOURSQUARE_CLIENT_SECRET, FOURSQUARE_REDIRECT_URI)
        url = api.build_url()
        return url


    @classmethod
    def get_access_token(self, oauth_code=None):
        print "get foursquare access token"
        api = Foursquare(FOURSQUARE_CLIENT_ID, FOURSQUARE_CLIENT_SECRET, FOURSQUARE_REDIRECT_URI)
        access_token = api.authorize(oauth_code=oauth_code)
        return access_token


    @classmethod
    def create_foursquare_client(self, access_token=None):
        print "create foursquare client..."
        api = Foursquare(FOURSQUARE_CLIENT_ID, FOURSQUARE_CLIENT_SECRET, FOURSQUARE_REDIRECT_URI)
        print "api ok"
        foursquare_client = api.create_client(access_token)
        return foursquare_client



class ApiError(Exception):
    pass
