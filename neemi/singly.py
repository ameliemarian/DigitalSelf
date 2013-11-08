# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

import requests
from webapp import settings
from webapp.settings import SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET, SINGLY_REDIRECT_URI

import httplib

def patch_http_response_read(func):
    def inner(*args):
        try:
            return func(*args)
        except httplib.IncompleteRead, e:
            print "NEEDED TO USE PATCH FUNCTION"
            return e.partial

    return inner
httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)


class Singly(object):

    api_base = 'https://api.singly.com'

    def __init__(self, client_id=None, client_secret=None, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token

    def make_request(self, endpoint, method='GET', request={}):
        url = self.api_base + endpoint
        print [url]
        print [request]
        #print [method]

        if method == 'GET':
            if self.access_token is not None:
                request['access_token'] = self.access_token
            response = requests.get(url, params=request)

        elif method == 'POST':
            response = requests.post(url, request)

        else:
            raise ApiError("Unsupported protocol")

        if response.status_code == 200:
            return json.loads(response.content)
        else:
            if settings.DEBUG:
                raise ApiError("%s: %s" % (response.status_code, response.content))
            else:
                raise ApiError("Error returned from API")

    def authorize(self, code):
        endpoint = '/oauth/access_token'
        request = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code
        }
        content = self.make_request(endpoint, 'POST', request)
        return content

    def register(self, user, password):
        endpoint = '/auth/password/register/'
        endpoint += self.client_id
        request = {
            #   'client_id': self.client_id,
            # 'client_secret': self.client_secret,
            'user': user,
            'password': password
        }
        content = self.make_request(endpoint, 'POST', request)
        return content

    def login(self, user, password):
        endpoint = '/auth/password/login/'
        endpoint += self.client_id
        request = {
            #   'client_id': self.client_id,
            # 'client_secret': self.client_secret,
            'user': user,
            'password': password
        }
        content = self.make_request(endpoint, 'POST', request)
        return content


class SinglyHelper(object):

    @classmethod
    def get_authorize_url(cls, service, token=None):

        url = '%s/oauth/authenticate?client_id=%s&redirect_uri=%s&service=%s' % (
            Singly.api_base, SINGLY_CLIENT_ID, SINGLY_REDIRECT_URI, service
        )
        if token:
            url += '&access_token=%s' % (token)
            #forces new login (maybe only on twitter and fb
        url += '&force_login=true'
        return url

    @classmethod
    def get_access_token(cls, code):
        print "get singly access token"
        api = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        print "api ok"
        content = api.authorize(code)
        print "content ok"
        print[content]
        return content

    @classmethod
    def create_singly_user(cls, user, password):
        print "create singly user"
        api = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        # print "api ok"
        content = api.register(user=user, password=password)
        print "registered"
        print[content]
        return content

    @classmethod
    def login_singly_user(cls, user, password):
        print "login singly user"
        api = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        # print "api ok"
        content = api.login(user=user, password=password)
        print "logged in"
        print[content]
        return content


    @classmethod
    def delete_singly_user(cls, user):
        print "delete singly user"
        api = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        # print "api ok"

        endpoint = '/profiles?delete='
        #endpoint += '1d8b16cf845d09602d1c60effdcba4d2'
        endpoint += user.get_singly_id()
        endpoint += '&access_token='
        #endpoint += 'z4aY_Ob5R45fUAhh3WLmYwShTkg.Y8C9U2tj63185b3f4fd7ad609e1bd498384987dd43046996156b72879146ae353eb56741b15b2466fab0720eff027a270a98cfb0bd3a3a54b4e9d770f47044bafe7445a018054116293e718235c6f2e90e7ed911a9a1cbb0f31ac155a4bec43b3dca3294'
        endpoint += user.get_access_token()
        request = {}
    
        singly_profile_deleted = api.make_request(endpoint=endpoint, method='POST', request=request)
        return singly_profile_deleted

    @classmethod
    def make_singly_request(cls, endpoint, method='GET', request={}):
        print "make singly request"
        api = Singly(SINGLY_CLIENT_ID, SINGLY_CLIENT_SECRET)
        # print "api ok"

        singly_request_result = api.make_request(endpoint=endpoint, method=method, request=request)
        return singly_request_result



class ApiError(Exception):
    pass
