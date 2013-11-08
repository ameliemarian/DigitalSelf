# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

import requests
import httplib
import urlparse
import oauth2 as oauth
import urllib

# Python wrapper for the Twitter API
# https://github.com/ryanmcgrath/twython
# pip install twython
from twython import Twython

from webapp import settings
from webapp.settings import TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_REDIRECT_URI

request_token_url='https://api.twitter.com/oauth/request_token'
access_token_url='https://api.twitter.com/oauth/access_token'
authorize_url='https://api.twitter.com/oauth/authorize'

class Twitter(object):

    api_base = 'https://api.twitter.com/'

    def __init__(self, consumer_key=None, consumer_secret=None, redirect_uri=None):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.redirect_uri = redirect_uri

    def build_url(self, request={}):

        # Get a request token. This is a temporary token that is used for 
        # having the user authorize an access token and to sign the request to obtain 
        # said access token.
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
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
        return url, request_token


    def authorize(self, oauth_verifier=None, request_token=None):
        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)

        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer, token)

        resp, content = client.request(access_token_url, "POST")
        access_token = dict(urlparse.parse_qsl(content))

        return access_token


#    def create_client(self,key,secret):
#        token = oauth.Token(key,secret)
#        consumer = oauth.Consumer(self.consumer_key, self.consumer_secret)
#        client = oauth.Client(consumer,token)
#        return client  

    def create_client(self,key,secret):
        client = Twython(self.consumer_key, self.consumer_secret, key, secret)
        return client


class TwitterHelper(object):

    def __init__(self, request_token=None):
        self.request_token = request_token

    @classmethod
    def get_authorize_url(self, service):
        print service
        api = Twitter(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_REDIRECT_URI)
        url, self.request_token = api.build_url()
        return url

    @classmethod
    def get_access_token(self, oauth_verifier):
        print "get twitter access token"
        api = Twitter(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_REDIRECT_URI)
        access_token = api.authorize(oauth_verifier=oauth_verifier, request_token=self.request_token)

        oauth_token = access_token['oauth_token']
        oauth_token_secret = access_token['oauth_token_secret']
        userid = access_token['user_id']
        screenname = access_token['screen_name']

        return oauth_token, oauth_token_secret, userid, screenname

    @classmethod
    def create_twitter_client(self, key, secret):
        print "create twitter client"
        api = Twitter(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET, TWITTER_REDIRECT_URI)
        twitter_client = api.create_client(key, secret)
        return twitter_client


class ApiError(Exception):
    pass
