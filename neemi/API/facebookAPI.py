from rauth.service import OAuth2Service
from webapp import settings
from webapp.settings import FACEBOOK_CLIENT_ID, FACEBOOK_CLIENT_SECRET, FACEBOOK_REDIRECT_URI

import urllib2 
import json 
from json import loads

class Facebook():

	def __init__(self):
		graph_url = 'https://graph.facebook.com/'
		fields = 'read_stream, email, user_education_history, user_likes, user_photos, user_relationships, user_work_history, user_activities, user_events, user_hometown, user_location, user_videos, user_birthday, user_interests, user_notes, user_relationship_details, user_status, user_groups, friends_status, friends_relationship_details, friends_education_history, friends_groups, friends_photos, friends_relationships, friends_work_history, friends_events, friends_hometown, friends_location, friends_videos, read_mailbox'

		self.name = 'facebook'
		self.authorize_url='https://www.facebook.com/dialog/oauth'
		self.access_token_url=graph_url + 'oauth/access_token'
		self.client_id = FACEBOOK_CLIENT_ID
		self.client_secret = FACEBOOK_CLIENT_SECRET
		self.scope = fields
		self.base_url = graph_url
		self.request_token = None

class FacebookHelper():

	__attrs__ = ['service', 'request_token']

	def __init__(self, request_token=None):
		facebook = Facebook()
        	self.service = OAuth2Service(name=facebook.name,
                         authorize_url=facebook.authorize_url,
                         access_token_url=facebook.access_token_url,
                         client_id=facebook.client_id,
                         client_secret=facebook.client_secret,
			 scope=facebook.scope,
                         base_url=facebook.base_url)

    	def get_authorize_url(self):
		params = {'redirect_uri': FACEBOOK_REDIRECT_URI}
    		authorize_url = self.service.get_authorize_url(**params)
    		return authorize_url

	def get_access_token(self, code):
		data = dict(code=code, redirect_uri=FACEBOOK_REDIRECT_URI)
		access_token = self.service.get_access_token(data=data)
		return access_token

	def get_user(self, access_token):
		url = 'https://graph.facebook.com/me?access_token=' + access_token
		f = urllib2.urlopen(url) 
		json_string = f.read() 
		user = loads(json_string)
		f.close()
		return user['id'], user['username']

	#check expiration
	def make_request(self, access_token, request, method='GET'):
        	url = 'https://graph.facebook.com/me?access_token='
        	print [url]
        	print [request]

        	if method == 'GET':
            		if access_token is not None:
            			url += access_token
				f = urllib2.urlopen(url) 
				json_string = f.read()
				response = loads(json_string)
				f.close()

        	if response.get('error') == None:
            		return response
        	else:
            		raise ApiError("%s: %s" % (response['error']['code'], response['error']['message']))
		
class ApiError(Exception):
    pass
