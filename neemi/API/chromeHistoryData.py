import time,datetime
import re
import optparse
import os
import sqlite3
import requests
import json

from pymongo import MongoClient
from neemi.models import *
from mongoengine.django.auth import User


try: import simplejson as json
except ImportError: import json



class ChromeHistoryData(object):

	def getChromeData(self, request={}, service=None):
		currentuser = User.objects.get(username=request.user.username)
		service_user, created = ChromeUser.objects.get_or_create(neemi_user=currentuser) 
		print service
		if service == 'chromeHistory':
			history = historyData(user=service_user)
			print history
			
			if history.getHistory():
				print 'getHistory IS true'
				# update date that firefox history was last accessed
				service_user.last_history_access = datetime.datetime.now()
				service_user.save()
		elif service == 'chromeSearchHistory':
			search = historySearchData(user=service_user)
			if search.getSearch():
				service_user.last_search_access = datetime.datetime.now()
				service_user.save()
		else:
			print 'Service does not exist!'


class historyData(object):

	def __init__(self, user=None):
		self.user = user
	
	def getHistory(self):
		print 'IM HERE!!'
		placesDB = '/Users/suitcase/Library/Application Support/Google/Chrome/Default/History'
		print placesDB
		if os.path.isfile(placesDB):
			self.printHistory(placesDB)
		else:
			print '[!] PlacesDb does not exist: ' + placesDB
			return False
		
		return True


	def printHistory(self, placesDB):
		try:
			print 'HERE'
			conn = sqlite3.connect(placesDB)
			c = conn.cursor()
			
			if (self.user.last_history_access == None):
				since = 0
			else:
				since = self.user.last_history_access
			
			
			print 'Since: ', since 
			query = """ select url, datetime(last_visit_time/1000000, 'unixepoch') \
			from urls \
			where datetime(last_visit_time/1000000, 'unixepoch') > ?; """
		
			data =  [since]
			c.execute(query, data)
			
			print '-- History --'
			for row in c:
				url = str(row[0])
				date = str(row[1])
				print date + ' -- Visited: ' + url
				if (url != ''):
					#data['data_type']='CHROME_HISTORY'
					data = date + ' -- ' + url
					self.storeData(data)
					print data
		except Exception, e:
			print e
			if 'encrypted' in str(e):
				print 'Error reading your places database.'
				print 'Upgrade your Python-Sqlite3 Library'
	
	def storeData(self, data=None):
		service_data = ChromeData.objects.create(neemi_user=self.user.neemi_user)
		service_data.data_type = 'HISTORY'
		service_data.chrome_user = self.user
		service_data.data = data
		service_data.save()

class historySearchData(object):

    def __init__(self, user=None):
        self.user = user   

    def getSearch(self):
        # path to sqlite database that contains the browser history 
        placesDB = '/Users/suitcase/Library/Application Support/Google/Chrome/Default/History'
        print placesDB
                                                                                                                                                                                                                                                                                                                                    
        if os.path.isfile(placesDB):
            self.printGoogle(placesDB)
        else:
            print '[!] PlacesDb does not exist: ' + placesDB
            return False
        return True

    def printGoogle(self, placesDB):
        conn = sqlite3.connect(placesDB)
        c = conn.cursor()

        if (self.user.last_search_access == None):
            since = 0
        else:
            since = self.user.last_search_access

        print 'Since: ', since 

        query = """ select url, datetime(last_visit_time/1000000, 'unixepoch') \
			from urls \
			where datetime(last_visit_time/1000000, 'unixepoch') > ?; """
        data =  [since]
        c.execute(query, data)

        print '-- Found Google --'
        for row in c:
            url = str(row[0])
            date = str(row[1])
            if 'google' in url.lower():
                r = re.findall(r'q=.*\&', url)
                if r:
                    search=r[0].split('&')[0]
                    search=search.replace('q=','').replace('+', ' ')
                    print date + ' -- Searched For: ' + search
                    if (search != ''):
                        self.storeData(data = date + ' -- ' + search)


    def storeData(self, data=None):
        service_data = ChromeData.objects.create(neemi_user=self.user.neemi_user)
        service_data.data_type = 'SEARCH_HISTORY'
        service_data.chrome_user = self.user
        service_data.data = data
        service_data.save()



		
		
