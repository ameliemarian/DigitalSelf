# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

import time,datetime
import os

# Python wrapper for the foursquare v2 API
# https://github.com/mLewisLogic/foursquare
# pip install foursquare
import foursquare

from neemi.models import *
from foursquareAPI import FoursquareHelper

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

# Number of results to return
checkin_limit = 250
friends_limit = 500
photos_limit = 500
recent_limit = 100

class FoursquareAPIData(object):

    def getFoursquareProfile(self, request):
        print "Get Profile Data from foursquare"            
        currentuser = User.objects.get(username=request.user.username)
        service_user = FoursquareUser.objects.get(neemi_user=currentuser)          
        print [service_user]
        print "done foursquare profile"
        return service_user


    def getFoursquareData(self, request, service):
        print "Get Data from " + service

        currentuser = User.objects.get(username=request.user.username)
        service_user = FoursquareUser.objects.get(neemi_user=currentuser)
        client = FoursquareHelper.create_foursquare_client(access_token=service_user.access_token)

# I am not storing profile yet
#        getProfile(client=client, service_user=service_user)

        getBadges(client=client, service_user=service_user)
        getCheckins(client=client, service_user=service_user)
        if (service_user.last_access == '0'):
            getALLFriends(client=client, service_user=service_user)
            getALLPhotos(client=client, service_user=service_user)
        else:
            getFriends(client=client, service_user=service_user)
            getPhotos(client=client, service_user=service_user)
        getRecent(client=client, service_user=service_user)
        
        service_user.last_access = timestamp()
        service_user.save()


def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y%m%d%H%M%S', localtime) + milliseconds

def getProfile(client=None, service_user=None):
    print "Starting getProfile... "

    data = client.users()


def getBadges(client=None, service_user=None):
    print "Starting getBadge... "

    data = client.users.badges()

    allbadges = []
    for item in data['badges']:
        allbadges.append(item)

    for item in allbadges:
        print item
        badge = data['badges'][item]
        storeData(data=badge, data_type='BADGE', service_user=service_user)



def getCheckins(client=None, service_user=None):
    print "Starting getCheckins... " 

    afterTimestamp = service_user.last_access
    print
    print "afterTimestamp: ", afterTimestamp
    print

    offset = 0
    params = {
        'offset': offset,
        'limit': checkin_limit,
        'afterTimestamp' : afterTimestamp
    }

    checkins = client.users.checkins(params=params) 

    checkins = checkins['checkins']
    if (checkins['count'] > 0):
        storeDataCollected(data=checkins['items'], data_type='CHECKIN', service_user=service_user)

    print "checkins: "
    print checkins
    print "Count: ", checkins['count']
    print "Items: ", checkins['items']

    while (checkins['count'] > 0):
        if (checkins['count'] < checkin_limit):
            break

        offset = checkins['count'] + checkin_limit
        params = {
            'offset': offset,
            'limit': checkin_limit,
            'afterTimestamp' : afterTimestamp
        }
        checkins = client.users.checkins(params=params)

        checkins = checkins['checkins']
        if (checkins['count'] > 0):
            storeDataCollected(data=checkins['items'], data_type='CHECKIN', service_user=service_user)

        

def getALLFriends(client=None, service_user=None):
    print "Starting getALLFriend... " 

    offset = 0
    params = {
        'offset': offset,
        'limit': friends_limit
    }
    friends = client.users.friends(params=params)

    friends = friends['friends']
    if (friends['count'] > 0):
        storeDataCollected(data=friends['items'], data_type='FRIEND', service_user=service_user)

    print "friends: "
    print friends
    print "Count: ", friends['count']
    print "Items: ", friends['items']

    while (friends['count'] > 0):
        if (friends['count'] < friends_limit):
            break

        offset = friends['count'] + friends_limit
        params = {
            'offset': offset,
            'limit': friends_limit,
        }
        friends = client.users.friends(params=params)

        friends = friends['friends']
        if (friends['count'] > 0):
            storeDataCollected(data=friends['items'], data_type='FRIEND', service_user=service_user)   

   
 
def getFriends(client=None, service_user=None):
    print "Starting getFriend... " 

    friends = client.users.friends()

    print "friends: "
    print friends
    print "Count: ", friends['count']
    print "Items: ", friends['items']
    storeDataCollected(data=friends['items'], data_type='FRIEND', service_user=service_user)



def getALLPhotos(client=None, service_user=None):
    print "Starting getALLPhotos... " 

    offset = 0
    params = {
        'offset': offset,
        'limit': photos_limit
    }
    photos = client.users.photos(params=params)

    photos = photos['photos']
    if (photos['count'] > 0):
        storeDataCollected(data=photos['items'], data_type='PHOTO', service_user=service_user)

    print "photos: "
    print photos
    print "Count: ", photos['count']
    print "Items: ", photos['items']

    while (photos['count'] > 0):

        if (photos['count'] < photos_limit):
            break

        offset = photos['count'] + photos_limit
        params = {
            'offset': offset,
            'limit': photos_limit,
        }
        photos = client.users.photos(params=params)

        photos = photos['photos']
        if (friends['count'] > 0):
            storeDataCollected(data=photos['items'], data_type='PHOTO', service_user=service_user)    



def getPhotos(client=None, service_user=None):
    print "Starting getPhoto... " 

    photos = client.users.photos()

    print "photos: "
    print photos
    print "Count: ", photos['count']
    print "Items: ", photos['items']
    storeDataCollected(data=photos['items'], data_type='PHOTO', service_user=service_user)



def getRecent(client=None, service_user=None):
    print "Starting getRecent... " 

    afterTimestamp = service_user.last_access
    print
    print "afterTimestamp: ", afterTimestamp
    print

    params = {
        'limit': recent_limit,
        'afterTimestamp' : afterTimestamp
    }
    recent = client.checkins.recent(params=params)

    recent = recent['recent']
    storeDataCollected(data=recent, data_type='RECENT', service_user=service_user)



# Store the data collected
def storeDataCollected(data=None, data_type=None, service_user=None):
    for item in data: 
        storeData(data=item, data_type=data_type, service_user=service_user)



def storeData(data=None, data_type=None, service_user=None):
    service_data, created = FoursquareData.objects.get_or_create(feed_id=data['id'],data_type=data_type,neemi_user=service_user.neemi_user)

    # If the data already exists, we update it
    service_data.data_type = data_type
    service_data.feed_id = data['id'] 
    if (data_type == 'BADGE') or (data_type == 'FRIEND'):
        service_data.time = datetime.datetime.now()
    elif (data_type == 'CHECKIN') or (data_type == 'RECENT') or (data_type == 'PHOTO'):
        service_data.time = datetime.datetime.fromtimestamp(data['createdAt'])
        #service_data.time = data['createdAt']
    service_data.foursquare_user = service_user
    service_data.data = data

    service_data.save()
        

