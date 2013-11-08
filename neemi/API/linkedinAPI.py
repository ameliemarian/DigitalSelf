
import requests
import oauth2 as oauth
import urllib
import urlparse

from webapp import settings
from webapp.settings import LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_REDIRECT_URI

request_token_url = 'https://api.linkedin.com/uas/oauth/requestToken'
authorize_url     = 'https://api.linkedin.com/uas/oauth/authorize'
access_token_url  = 'https://api.linkedin.com/uas/oauth/accessToken'
authenticate_url  = 'https//www.linkedin.com/uas/oauth/authenticate'

class LinkedIn(object):

    def __init__(self, api_key=None, api_secret=None, redirect_uri=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri

    def build_url(self, request={}):
        # Get a request token. This is a temporary token that is used for 
        # having the user authorize an access token and to sign the request to obtain 
        # said access token.
        consumer = oauth.Consumer(self.api_key, self.api_secret)
        client = oauth.Client(consumer)

        resp, content = client.request(request_token_url, "POST", body=urllib.urlencode({'oauth_callback':self.redirect_uri}))

        print content 

        if resp['status'] != '200':
            if settings.DEBUG:
                raise ApiError("%s: %s" % (resp['status'], resp['content']))
            else:
                raise ApiError("Error returned from API")

        request_token = dict(urlparse.parse_qsl(content))

        # Redirect the user to the authentication URL.
        url = "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
        print "url = %s" % url
        return url, request_token 


    def authorize(self, oauth_verifier=None, request_token=None):
        print "authorize... "
        consumer = oauth.Consumer(self.api_key, self.api_secret)
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer, token)

        resp, content = client.request(access_token_url, "POST")
        access_token = dict(urlparse.parse_qsl(content))

        return access_token 


    def create_client(self, access_key=None, access_secret=None):
        consumer = oauth.Consumer(self.api_key, self.api_secret)    
        token = oauth.Token(key=access_key, secret=access_secret)
        client = oauth.Client(consumer, token)
        return client  

    
    def refresh_token(self): 
        # Get a request token
        consumer = oauth.Consumer(self.api_key, self.api_secret)
        client = oauth.Client(consumer)

        resp, content = client.request(request_token_url, "POST", body=urllib.urlencode({'oauth_callback':self.redirect_uri}))

        if resp['status'] != '200':
            if settings.DEBUG:
                raise ApiError("%s: %s" % (resp['status'], resp['content']))
            else:
                raise ApiError("Error returned from API")

        request_token = dict(urlparse.parse_qsl(content))

        url = "%s?oauth_token=%s" % (authorize_url, request_token['oauth_token'])
        resp, content = client.request(url, "POST")
        access_token = dict(urlparse.parse_qsl(content))

        return access_token        


class LinkedInHelper(object):

    def __init__(self, request_token=None):
        self.request_token = request_token

    @classmethod
    def get_authorize_url(self, service=None):
        print service
        api = LinkedIn(LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_REDIRECT_URI)
        url, self.request_token = api.build_url()
        return url

    @classmethod
    def get_access_token(self, oauth_verifier=None):
        print "get linkedin access token"
        api = LinkedIn(LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_REDIRECT_URI)
        access_token = api.authorize(oauth_verifier=oauth_verifier, request_token=self.request_token)

        oauth_token = access_token['oauth_token']
        oauth_token_secret = access_token['oauth_token_secret']
        oauth_expires_in = access_token['oauth_expires_in']
        return oauth_token, oauth_token_secret, oauth_expires_in

    @classmethod
    def create_linkedin_client(self, key=None, secret=None):
        print "create linkedin client"
        api = LinkedIn(LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_REDIRECT_URI)
        print "api ok"
        linkedin_client = api.create_client(key, secret)
        return linkedin_client

    def refresh_access_token(self):
        api = LinkedIn(LINKEDIN_API_KEY, LINKEDIN_API_SECRET, LINKEDIN_REDIRECT_URI)
        access_token = api.refresh_token()
        oauth_token = access_token['oauth_token']
        oauth_token_secret = access_token['oauth_token_secret']
        oauth_expires_in = access_token['oauth_expires_in']
        return oauth_token, oauth_token_secret, oauth_expires_in



class ApiError(Exception):
    pass
