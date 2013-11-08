import time,datetime
import os
import json

import requests
import oauth2 as oauth

from django.http import HttpResponseRedirect, HttpResponse
from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

#from webapp import settings
from neemi.models import *
from linkedinAPI import LinkedInHelper

def enum(**enums):
    return type('Enum', (), enums)

ENDPOINTS = enum(PEOPLE='https://api.linkedin.com/v1/people',
                 GROUPS='https://api.linkedin.com/v1/groups',
                 COMPANIES='https://api.linkedin.com/v1/companies')

headers = {'x-li-format': 'json', 'Content-Type': 'application/json'}
args = dict(headers=headers)

max_updates = 250
max_connections = 500

def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y%m%d%H%M%S', localtime) + milliseconds

class LinkedInAPIData(object):

    def getLinkedInProfile(self, request):
        print "Get Profile Data from linkedin"
            
        currentuser = User.objects.get(username=request.user.username)
        service_user = LinkedInUser.objects.get(neemi_user=currentuser)       
    
        print [service_user]
        print "done linkedin profile"
        return service_user


    def getLinkedInData(self, request, service):
        print "Get Data from " + service

        currentuser = User.objects.get(username=request.user.username)
        service_user = LinkedInUser.objects.get(neemi_user=currentuser)

        # check is access token is expired
#        if (current_user.access_token_expires_at == '0') or (int(time.time()) > current_user.access_token_expires_at == '0'):
#            print "Linkedin access token is expired!"
#            print "Refreshing Linkedin access token..."
#            current_linkedin_helper = LinkedInHelper()
#            access_token, access_token_secret, oauth_expires_in = current_linkedin_helper.refresh_access_token()
            # Store new access token and expiration time
#            linkedinuser.access_token_key = access_token
#            linkedinuser.access_token_secret = access_token_secret
#            linkedinuser.access_token_expires_in = oauth_expires_in
#            linkedinuser.access_token_expires_at = int(time.time()) + oauth_expires_in
#            linkedinuser.save()
        

        client = LinkedInHelper.create_linkedin_client(service_user.access_token_key, service_user.access_token_secret)

        # To retrieve authenticated user profile
        getProfile(client=client, service_user=service_user)
        # Returns a list of 1st degree connections for a user who has granted access to his/her account
        getConnections(client=client, service_user=service_user)
        # To retrieve the member's first-degree connection updates
        getNetworkUpdates(client, service_user=service_user)
        # To retrieve the member's updates
        getUserUpdates(client, service_user=service_user)

        service_user.modified_since = timestamp()
        print service_user.modified_since
        service_user.save()
        
        #getCompanies(client, company_id=company_id)
        #getJobBookmarks(client)
        #getNetworkStat(client=client)
        #getMemberships(client, modified_since=service_user.modified_since)


def storeDataCollected(data=None, data_type=None, service_user=None):
    for item in data['values']: 
        storeData(data=item, data_type=data_type, service_user=service_user)


def storeData(data=None, data_type=None, service_user=None):

#    print "Storing %s..." % data_type

    if (data_type == 'PROFILE'):
        data_id = data['id']
#        data_time = datetime.datetime.now()
    elif (data_type == 'CONNECTION'): 
        data_id = data['id']
#        data_time = datetime.datetime.fromtimestamp(data['currentShare']['timestamp']/1000)
#        print data_time
    elif (data_type == 'UPDATE') or (data_type == 'NETWORK'):
        data_id = data['updateKey']
#        data_time = datetime.datetime.fromtimestamp(data['timestamp']/1000)

    service_data, created = LinkedInData.objects.get_or_create(data_type=data_type,feed_id=data_id,neemi_user=service_user.neemi_user)
#    if created == True:
    # If the data already exists, we update it
    service_data.data_type = data_type
    service_data.feed_id = data_id
    service_data.time = datetime.datetime.now()
    service_data.linkedin_user = service_user
    service_data.data = data
    service_data.save()


def getData(client=None, url=None):
    response, content = client.request(url, **args)
    if response.status == 200:
        return response, content   
    else:
        if settings.DEBUG:
            raise ApiError("%s" % (content))
        else:
            raise ApiError("Error returned from API")


def getProfile(client=None, service_user=None):
    print "Starting getProfile... "

    # Full profile fields
    profile_fields = "id,first-name,last-name,headline,current-share,num-connections,location:(name),summary,specialties,positions,picture-url,skills:(id),languages,educations,last-modified-timestamp,proposal-comments,associations,interests,publications,patents,certifications,courses,volunteer,three-current-positions,three-past-positions,num-recommenders,recommendations-received,mfeed-rss-url,following,job-bookmarks,suggestions,date-of-birth,member-url-resources,related-profile-views"

    url = "%s/~/network/updates?scope=self&type=PRFU" % (ENDPOINTS.PEOPLE)
    print "Url: ", url      
    response, content = getData(client=client, url=url)
    data = json.loads(content)
        
    print "Total: ", data['_total']
    print "Modified since: ", service_user.modified_since
    if (data['_total'] != 0) or (service_user.modified_since == "0"):
        url = '%s/~:(%s)' % (ENDPOINTS.PEOPLE, profile_fields)    
        response, content = getData(client=client, url=url)
        data = json.loads(content)
        storeData(data, 'PROFILE', service_user)
        


def getConnections(client=None, service_user=None):
    print "Starting getConnections... "

    # Basic profile fields
    profile_fields = "id,first-name,last-name,headline,location:(name),industry,current-share,num-connections,summary,specialties,positions,picture-url"

    url = '%s/~/connections:(%s)?modified=updated&modified-since=%s&count=%s' % (ENDPOINTS.PEOPLE, profile_fields, service_user.modified_since, max_connections)    
    response, content = getData(client=client, url=url)
    data = json.loads(content)
    if (data['_total'] == 0):
        return
    storeDataCollected(data, 'CONNECTION', service_user)



def getMemberships(client=None, modified_since=None):
    print "Starting getMemberships... "

    group_id_list = []

    url = '%s/~/group-memberships?count=%s&start=0' % (ENDPOINTS.PEOPLE, max_retrieved)     
    response, content = getData(client=client, url=url)

    # SAVE ALL GROUPS FROM GETMEMBERSHIP (CONTENT)

    groups = json.loads(content)
    for g in groups['values']: 
        group_id_list.append(g['group']['id'])

    # I have to improve the retrieval of groups and posts
    # For now, I am always getting the entire list of groups every time a user
    # request new data. From the list of users I request new posts since my last call.
    for item in group_id_list:
        print getGroups(client, item)
        print getGroupPosts(client, item, modified_since)


def getJobBookmarks(client=None):
    print "Starting getJobBookmarks... "

    url = '%s/~/job-bookmarks' % ENDPOINTS.PEOPLE    
    getData(client=client, url=url)


def getNetworkUpdates(client=None, service_user=None):
    print "Starting getNetwokUpdates... "

    url = '%s/~/network/updates?after=%s&count=%d' % (ENDPOINTS.PEOPLE, service_user.modified_since, max_updates)    
    response, content = getData(client=client, url=url)
    data = json.loads(content)
    if (data['_total'] == 0):
        return
    storeDataCollected(data, 'UPDATE', service_user)


def getUserUpdates(client=None, service_user=None):
    print "Starting getUserUpdates... "

    url = '%s/~/network/updates?scope=self&after=%s&count=%d' % (ENDPOINTS.PEOPLE, service_user.modified_since, max_updates)    
    response, content = getData(client=client, url=url)
    data = json.loads(content)

    if (data['_total'] == 0):
        return
    storeDataCollected(data, 'NETWORK', service_user)


def getNetworkStat(client=None):
    print "Starting getNetwokStatus... "

    url = '%s/~/network/network-stats' % ENDPOINTS.PEOPLE     
    getData(client=client, url=url)
 

def getGroups(client=None, group_id=None):
    print "Starting getGroups... "

    url = '%s/%s' % (ENDPOINTS.GROUPS, str(group_id))   
    getData(client=client, url=url)


def getGroupPosts(client=None, group_id=None, modified_since=None):
    print "Starting getGroupPosts (Posts a User has Participated in for a Group)... "

    profile_fields = "creator:(first-name,last-name,picture-url),title,summary,creation-timestamp,likes,comments,attachment:(image-url,content-domain,content-url,title,summary)"
    url = '%s/%s/posts:(%s)?role=commenter&category=discussion&modified-since=%s&count=%s' % (ENDPOINTS.GROUPS, str(group_id), profile_fields, modified_since, max_retrieved)   
    getData(client=client, url=url)


def getCompanies(client=None, company_id=None):
    print "Starting getCompanies... "

    profile_fields = "name,id,website-url,twitter-id,employee-count-range,specialties,locations,description,founded-year,end-year,num-followers"
    url = "%s/%s:(%)" % (ENDPOINTS.COMPANIES, company_id, profile_fields)    
    getData(client=client, url=url)


class ApiError(Exception):
    pass

