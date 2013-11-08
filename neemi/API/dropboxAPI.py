# Dropbox module
# https://www.dropbox.com/developers/core/sdks/python
# pip install dropbox
from dropbox import client, rest, session

# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

from webapp import settings
from webapp.settings import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, DROPBOX_REDIRECT_URI

class Dropbox(object):

    def __init__(self, app_key=None, app_secret=None, access_type=None, redirect_uri=None, sess=None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_type = access_type
        self.redirect_uri = redirect_uri

    def build_url(self):
        sess = session.DropboxSession(self.app_key, self.app_secret, self.access_type)
        request_token = sess.obtain_request_token()
        sess.set_request_token(request_token.key, request_token.secret)
        url = sess.build_authorize_url(request_token, oauth_callback=self.redirect_uri)
        return url, sess

    def authorize(self, sess=None):
        access_token = sess.obtain_access_token()
        return access_token

    def create_client(self,key,secret):
        sess = session.DropboxSession(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE)
        sess.set_token(key,secret) 
        dropbox_client = client.DropboxClient(sess) 
        return dropbox_client  


class DropboxHelper(object):

    def __init__(self, sess=None):
        self.sess = None

    @classmethod
    def get_authorize_url(self, service):
        print service
        api = Dropbox(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, DROPBOX_REDIRECT_URI)
        url, self.sess = api.build_url()
        return url

    @classmethod
    def get_access_token(self):
        print "get dropbox access token"
        api = Dropbox(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, DROPBOX_REDIRECT_URI)
        access_token = api.authorize(sess=self.sess)
        return access_token

    @classmethod
    def create_dropbox_client(self, key, secret):
        print "create dropbox client"
        api = Dropbox(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, DROPBOX_REDIRECT_URI)
        dropbox_client = api.create_client(key, secret)
        return dropbox_client


