# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

import time,datetime
import os

# Python wrapper for the Twitter API
# https://github.com/ryanmcgrath/twython
# pip install twython
from twython import Twython, TwythonError

from neemi.models import *
from twitterAPI import TwitterHelper

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

max_count = 200

class TwitterAPIData(object):

    def getTwitterProfile(self, request):
        print "Get Profile Data from twitter"
            
        currentuser = User.objects.get(username=request.user.username)
        print "currentuser: ", currentuser
        service_user = TwitterUser.objects.get(neemi_user=currentuser)       
    
        print [service_user]
        print "done twitter profile"
        return service_user



    def getTwitterData(self, request, service):
        print "Get Data from " + service

        currentuser = User.objects.get(username=request.user.username)
        service_user = TwitterUser.objects.get(neemi_user=currentuser)

        client = TwitterHelper.create_twitter_client(service_user.access_token_key, service_user.access_token_secret)
    
        if (service_user.since_id == 0):
            # Mentions
            getData_ALL(data_type='MENTION', client=client, service_user=service_user)
            # Favorites
            getData_ALL(data_type='FAVORITE', client=client, service_user=service_user)
            # User timeline
            getData_ALL(data_type='TWEET', client=client, service_user=service_user)
            # Retweet
            getData_ALL(data_type='RETWEET', client=client, service_user=service_user)
            # Direct message - received
            getData_ALL(data_type='MSG_RECEIVED', client=client, service_user=service_user)
            # Direct message - sent
            getData_ALL(data_type='MSG_SENT', client=client, service_user=service_user)
            # Home timeline
            getData_ALL(data_type='TIMELINE', client=client, service_user=service_user)
        else:
            # Mentions
            getData_SINCE(data_type='MENTION', client=client, service_user=service_user)
            # Favorites
            getData_SINCE(data_type='FAVORITE', client=client, service_user=service_user)
            # User timeline
            getData_SINCE(data_type='TWEET', client=client, service_user=service_user)
            # Retweet
            getData_SINCE(data_type='RETWEET', client=client, service_user=service_user)
            # Direct message - received
            getData_SINCE(data_type='MSG_RECEIVED', client=client, service_user=service_user)
            # Direct message - sent
            getData_SINCE(data_type='MSG_SENT', client=client, service_user=service_user)
            # Home timeline
            getData_SINCE(data_type='TIMELINE', client=client, service_user=service_user)
        # followers
        get_Followers(client=client, service_user=service_user)
        # friends
        get_Friends(client=client, service_user=service_user)      
    


def getData(client=None, data_type=None, since_id=None, max_id=None, count=None):
    try:
        if data_type == 'TIMELINE':
            return client.get_home_timeline(since_id=since_id, max_id=max_id, count=count)
        elif data_type == 'MENTION':
            return client.get_mentions_timeline(since_id=since_id, max_id=max_id, count=count)
        elif data_type == 'FAVORITE':
            return client.get_favorites(since_id=since_id, max_id=max_id, count=count)
        elif data_type == 'TWEET':
            return client.get_user_timeline(since_id=since_id, max_id=max_id, count=count)     
        elif data_type == 'RETWEET':
            return client.retweeted_of_me(since_id=since_id, max_id=max_id, count=count)   
        elif data_type == 'MSG_RECEIVED':
            return client.get_direct_messages(since_id=since_id, max_id=max_id, count=count) 
        elif data_type == 'MSG_SENT':
            return client.get_sent_messages(since_id=since_id, max_id=max_id, count=count) 
    except TwythonError as e:
        print e     
    


# should be entered in the format year-month-day or yyyy-mm-dd.
# are assumed to be from/to 00:00 UTC.
#def get_HomeTimeline_RANGE(client=None, since=None, until=None, service_user=None):
#    query = "since:%s until:%s" % since, until
#    new_tweets = client.search(q=query)
#    # save id of the most recent tweet
#    service_user.since_id = alltweets[len(new_tweets)-1].id
#    service_user.save()zZ
#    storeDataCollected(new_tweets=new_tweets, tweet_type='TIMELINE', service_user=service_user)



def getData_SINCE(client=None, service_user=None, data_type=None):

    print "Starting getData_SINCE: ", data_type

    lastcall = service_user.since_id
    print "lastcall: ", str(lastcall)

    # try to get all tweets (home timeline, favorites, mentions...) since last call
    new_tweets = getData(client=client, data_type=data_type, since_id=lastcall, count=max_count)

    #save most recent tweets
    alltweets = []
    alltweets.extend(new_tweets)

    if not new_tweets:
        return

    # save id of the most recent tweet (only if data_type is home_timeline)
    if data_type == 'TIMELINE':
        service_user.since_id = alltweets[len(new_tweets)-1]['id']
        service_user.save()

    if (lastcall != 0):
        #save the id of the oldest tweet less one
        oldest = alltweets[-1]['id'] - 1
    
        #keep grabbing tweets until there are no tweets left to grab
        while (oldest > lastcall):
            new_tweets = getData(client=client, data_type=data_type,since_id=lastcall,max_id=oldest,count=max_count)
            if not new_tweets:
                break

            #save most recent tweets
            alltweets.extend(new_tweets)
            #update the id of the oldest tweet less one
            oldest = alltweets[-1]['id'] - 1
            print "...%s tweets downloaded so far" % (len(alltweets))
    # store data collected
    storeDataCollected(new_tweets=alltweets, tweet_type=data_type, service_user=service_user)



# get all tweets from an user timeline
def getData_ALL(client=None, service_user=None, data_type=None):
    print "Starting getData_ALL: ", data_type

    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = getData(client=client, data_type=data_type, count=max_count) 

    #save most recent tweets
    alltweets = []
    alltweets.extend(new_tweets)

    if not new_tweets:
        return

    # save id of the most recent tweet (only if data_type is home_timeline)
    if data_type == 'TIMELINE':
        service_user.since_id = alltweets[len(new_tweets)-1]['id']
        service_user.save()

    #save the id of the oldest tweet less one
    oldest = alltweets[-1]['id'] - 1
    newest = alltweets[len(new_tweets)-1]['id']

    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        print "getting tweets before %s" % (oldest)
        #all subsequent requests use the max_id param to prevent duplicates
        new_tweets = getData(client=client, data_type=data_type, count=max_count, max_id=oldest)
        if not new_tweets:
            break

        #save most recent tweets
        alltweets.extend(new_tweets)
        #update the id of the oldest tweet less one
        oldest = alltweets[-1]['id'] - 1
        print "...%s tweets downloaded so far" % (len(alltweets))
    # store data collected
    storeDataCollected(new_tweets=alltweets, tweet_type=data_type, service_user=service_user)



# Returns a list of users following the specified user
def get_Followers(client=None, service_user=None):
    print "Starting get_Followers..."
    try:
        followers = client.get_followers_list(count=max_count)
        for f in followers['users']:
            storeData(f, data_type='FOLLOWER', service_user=service_user)
    except TwythonError as e:
        print e 

  

# Returns a list of user's friends
def get_Friends(client=None, service_user=None):
    print "Starting get_Friends..."
    try:
        friends = client.get_friends_list(count=max_count)
        for f in friends['users']:
            storeData(f, data_type='FRIEND', service_user=service_user)
    except TwythonError as e:
        print e 

 

# Returns user's favorites
def get_Favorites(client=None, service_user=None):
    print "Starting get_Favorites..."
    try:
        favorites = get_favorites()
        for f in favorites:
            storeData(data=f, data_type='FAVORITE', service_user=service_user)
    except TwythonError as e:
        print e 



# Store the data collected
def storeDataCollected(new_tweets=None, tweet_type=None, service_user=None):
    for tweet in new_tweets:
        storeData(data=tweet, data_type=tweet_type, service_user=service_user)



def storeData(data=None, data_type=None, service_user=None):
    try:
        service_data, created = TwitterData.objects.get_or_create(feed_id=data['id_str'],data_type=data_type,neemi_user=service_user.neemi_user)
#    if created == True:
    # If the data already exists, we update it
        service_data.data_type = data_type
        service_data.feed_id = data['id_str']  
        service_data.time = data['created_at'] 
        service_data.twitter_user = service_user
        service_data.data = data
        service_data.save()
    except Exception as e:
        print 'Error trying to save twitter data - ', e    





    
