# The Google Contacts API can't be used with the google-api-python-client library because 
# it is a Google Data API, while google-api-python-client is intended to be used with 
# discovery-based APIs.

import httplib2
import sys

# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

# Google APIs Client Library for Python
# https://developers.google.com/api-client-library/python/start/installation
# pip install --upgrade google-api-python-client
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.file import Storage
from oauth2client.tools import run
from apiclient.discovery import build

# Google Data API
# pip install gdata
import atom
from atom.http import ProxiedHttpClient

import atom.data
import gdata.data
import gdata.contacts.client
import gdata.contacts.data


import imaplib
#import oauth2.clients.imap as imaplib

#from models import *
from neemi.models import *

from webapp import settings
from webapp.settings import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI

gprofile_scope  = 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email'
gdrive_scope    = 'https://www.googleapis.com/auth/drive.readonly'
gcal_scope      = 'https://www.googleapis.com/auth/calendar.readonly'
gplus_scope     = 'https://www.googleapis.com/auth/plus.login'
gmail_scope     = 'https://mail.google.com/'
gcontacts_scope = 'https://www.google.com/m8/feeds'

gcontacts_url   = 'http://www.google.com/m8/feeds/contacts/default/full'



OAUTH_LABEL='OAuth '

#Transforms OAuth2 credentials to OAuth2 token.
class OAuthCred2Token(object):

    def __init__(self, token_string):
        self.token_string = token_string

    def modify_request(self, http_request):
        http_request.headers['Authorization'] = '%s%s' % (OAUTH_LABEL,
                                                          self.token_string)
    ModifyRequest = modify_request



class Google(object):

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def build_url(self, request={}, service=None):

        scope = gprofile_scope

        currentuser = NeemiUser.objects.get(username=request.user.username)
        print [currentuser.services]
        if service == 'gcal' or  currentuser.has_google_service('gcal'):
            scope += ' ' + gcal_scope  
        if service == 'googledrive' or currentuser.has_google_service('googledrive'):
            scope += ' ' + gdrive_scope 
        if service == 'googleplus' or currentuser.has_google_service('googleplus'):
            scope += ' ' + gplus_scope  
        if service == 'gmail' or currentuser.has_google_service('gmail'):
            scope += ' ' + gmail_scope 
        if service == 'googlecontacts' or currentuser.has_google_service('googlecontacts'):
            scope += ' ' + gcontacts_scope         
   

        flow = OAuth2WebServerFlow(client_id=self.client_id, client_secret=self.client_secret, scope=scope, redirect_uri=self.redirect_uri, access_type='offline', approval_prompt='force')
        authorize_url = flow.step1_get_authorize_url()

        return authorize_url, flow


    def authorize(self, code=None, flow=None):
        credentials = flow.step2_exchange(code)       
        storage = Storage('credentials.dat')
        storage.put(credentials)     
        return credentials

    
    def createAuthorizedHTTP(self):
        storage = Storage('credentials.dat')
        credentials = storage.get()

        print "===> Credentials: ", credentials.to_json()

        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()

        if credentials is None:
            #TODO: print exception or authorize user
            print "Credentials does not exist!"
        if credentials.invalid:
            print "Refresh credentials(createAuthorizedHTTP)..."
            print "Credentials (Before refresh):"
            print credentials.to_json()
            credentials.refresh(http)
            print "Credentials (After refresh):"
            print credentials.to_json()

        # authorize http with credentials
        http = credentials.authorize(http)

        return http


    def getCredentials(self):
        storage = Storage('credentials.dat')
        credentials = storage.get()
        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()
        if credentials is None:
            #TODO: print exception or authorize user
            print "Credentials does not exist!"
        if credentials.invalid:
            print "Refresh credentials(getCredentials)..."
            credentials.refresh(http)

        # authorize http with credentials
        http = credentials.authorize(http)
        return credentials


    def refreshCredentials(self):
        storage = Storage('credentials.dat')
        credentials = storage.get()
        # Create an httplib2.Http object and authorize it with our credentials
        http = httplib2.Http()        
        credentials.refresh(http)
        return credentials


    def getUserProfile(self):
        http = self.createAuthorizedHTTP()
        client = build('oauth2', 'v2', http=http)
        user_document = client.userinfo().get().execute()
        return user_document   


    def create_GcalClient(self):
        http = self.createAuthorizedHTTP()
        client = build('calendar', 'v3', http=http)
        return client


    def create_GdriveClient(self):
        http = self.createAuthorizedHTTP()
        client = build('drive', 'v2', http=http)
        return client


    def create_GplusClient(self):
        http = self.createAuthorizedHTTP()
        client = build('plus', 'v1', http=http)
        return client


    def create_gmailClient(self, email=None):
        print "Creating gmail client..."
        credentials = self.getCredentials()
        #credentials = self.refreshCredentials()
        print "Credentials: ", credentials.to_json()
        access_token = credentials.access_token

        auth_string = 'user=%s\1auth=Bearer %s\1\1' % (email, access_token)
        #print "auth_string: ", auth_string

        imap_conn = imaplib.IMAP4_SSL('imap.gmail.com')
        imap_conn.debug = 4
        imap_conn.authenticate('XOAUTH2', lambda x: auth_string)

        return imap_conn


    def create_contactsClient(self):
        print "Creating contacts client..."
        credentials = self.getCredentials()
        access_token = credentials.access_token

        client = gdata.contacts.client.ContactsClient(source='neemiGetContext', alt='json')
        token = OAuthCred2Token(access_token)
        client.auth_token = token
        return client


class GoogleHelper(object):

    def __init__(self, flow=None):
        self.flow = None

    @classmethod
    def get_authorize_url(self, request=None, service=None):
        api = Google(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        url, self.flow = api.build_url(request=request, service=service)
        return url

    @classmethod
    def get_access_token(self, code):
        print "get google access token"
        api = Google(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        credentials = api.authorize(code=code, flow=self.flow)

    def get_userProfile(self):
        print "Get user profile!"
        api = Google(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        return api.getUserProfile()

    @classmethod
    def create_google_client(self, service=None, user=None):
        print "create google client: ", service
        api = Google(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI)
        print "api ok"
        if service == 'gcal':
            google_client = api.create_GcalClient()
        elif service == 'googledrive':
            google_client = api.create_GdriveClient()
        elif service == 'googleplus':
            google_client = api.create_GplusClient()
        elif service == 'gmail':
            google_client = api.create_gmailClient(email=user.email_address)
        elif service == 'googlecontacts':
            google_client = api.create_contactsClient()
        else:
            print "ERROR: Service not implemented!!!"
        return google_client

        




