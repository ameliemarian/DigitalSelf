# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

import requests
from webapp import settings
from webapp.settings import PLAID_CLIENT_ID, PLAID_CLIENT_SECRET, PLAID_REDIRECT_URI

import httplib



class Plaid(object):

    api_base = 'https://api.plaid.io'
    connect_base = 'https://connect.plaid.io'

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authorize(self, code):
        endpoint = '/oauth/access_token'
        request = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri' : self.redirect_uri,
            'code': code
        }
        url = self.connect_base + endpoint
        print [url]
        response = requests.post(url, request)
        if response.status_code == 200:
            return json.loads(response.content)
        else:
            if settings.DEBUG:
                raise ApiError("%s: %s" % (response.status_code, response.content))
            else:
                raise ApiError("Error returned from API")


    def make_request(self, method='GET', request={}):
        endpoint = 'connect/submit'
        url = self.api_base + endpoint
        print [url]
        request['client_id']=self.client_id
        print [request]
        #print [method]

        response = requests.get(url, params=request)

        if method == 'GET':
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

class PlaidHelper(object):

    @classmethod
    def get_authorize_url(cls):
        url = '%s/oauth/authorize?client_id=%s&redirect_uri=%s' % (
            Plaid.connect_base, PLAID_CLIENT_ID, PLAID_REDIRECT_URI)
        return url

    @classmethod
    def get_access_token(cls, code):
        print "get plaid access token"
        api = Plaid(PLAID_CLIENT_ID, PLAID_CLIENT_SECRET,PLAID_REDIRECT_URI)
        print "api ok"
        content = api.authorize(code)
        print "content ok"
        print[content]
        return content


    @classmethod
    def make_plaid_request(cls, method='GET', request={}):
        print "make plaid request"
        api = Plaid(PLAID_CLIENT_ID, PLAID_CLIENT_SECRET,PLAID_REDIRECT_URI)
        # print "api ok"

        plaid_request_result = api.make_request(method=method, request=request)
        return plaid_request_result



class ApiError(Exception):
    pass
