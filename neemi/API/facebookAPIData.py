from neemi.models import *
import urllib2
import json
from bson.json_util import loads
from datetime import datetime, time

from time import mktime
import calendar
from operator import *


def unix_time(dt):
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return long(delta.total_seconds())


def get_data(request, currentuser, service_user):
    print request
    if request.get('since') is not None:
        fromtimestamp = request.get('since')
        fromtimestamp = fromtimestamp/1000
    else:
        fromtimestamp = None
    if request.get('until') is not None:
        totimestamp = request.get('until')
        #dt = datetime.datetime.fromtimestamp(totimestamp)
        #totimestamp = dt.replace(microsecond=0)
        totimestamp = totimestamp/1000
    else:
        #totimestamp = calendar.timegm(datetime.today().utctimetuple())
        #totimestamp = unix_time(datetime.today())
        totimestamp = datetime.today().strftime('%s')

    print "fromtimestamp: ", fromtimestamp
    print "totimestamp: ", totimestamp

    data = []
    latestFirst = True
    if fromtimestamp is not None:
        latestFirst = False
    events = get_events(fromtimestamp, totimestamp, request.get('access_token'))
    events.sort(key=itemgetter('start_time'), reverse=latestFirst)
    inbox = get_inbox(fromtimestamp, totimestamp, request.get('access_token'))
    #inbox=[]
    feed = get_user_wall(fromtimestamp, totimestamp, request.get('access_token'))
    feed.sort(key=itemgetter('created_time'), reverse=latestFirst)
    photos = get_photos(fromtimestamp, totimestamp, request.get('access_token'))
    photos.sort(key=itemgetter('created_time'), reverse=latestFirst)
    home = get_standard_data('home', fromtimestamp, totimestamp, request.get('access_token'))
    home.sort(key=itemgetter('created_time'), reverse=latestFirst)
    #notes =get_standard_data('notes', fromtimestamp, totimestamp, request.get('access_token'))
    #notes.sort(key=itemgetter('created_time'), reverse=latestFirst)
    statuses = get_standard_data('statuses', fromtimestamp, totimestamp, request.get('access_token'))
    statuses.sort(key=itemgetter('updated_time'), reverse=latestFirst)
    links = get_standard_data('links', fromtimestamp, totimestamp, request.get('access_token'))
    links.sort(key=itemgetter('created_time'), reverse=latestFirst)
    posts = get_standard_data('posts', fromtimestamp, totimestamp, request.get('access_token'))
    posts.sort(key=itemgetter('created_time'), reverse=latestFirst)
    friends = get_friends(request.get('access_token'))
    groups = get_groups(request.get('access_token'))
    albums = get_standard_data('albums', fromtimestamp, totimestamp, request.get('access_token'))
    albums.sort(key=itemgetter('created_time'), reverse=latestFirst)


    data = process_data(request=request, currentuser=currentuser, service_user=service_user, data=data, events=events, feed=feed,
            photos=photos, home=home, statuses=statuses, links=links, posts=posts, friends=friends, groups=groups, albums=albums, inbox=inbox)

    return data

def process_data(request, currentuser, service_user, data, events, feed, photos, home, statuses, links, posts, friends, groups, albums, inbox):
    queue = []
    queue.append(events)
    queue.append(feed)
    queue.append(photos)
    queue.append(home)
    #queue.append(notes)
    queue.append(links)
    queue.append(statuses)
    queue.append(posts)
    queue.append(friends)
    queue.append(groups)
    queue.append(albums)
    queue.append(inbox)

    count = 0
    while len(data) < request.get('limit') and len(queue) > 0:
        category = queue.pop(0)
        item = None
        idr = None
        data_type = None
        if len(category) > 0:
            if category == events:
                item = category.pop(0)
                events = category
                idr = 'event:%s@facebook/events#%s'%(service_user.userid, item['id'])
                data_type = 'EVENT'
            elif category == feed:
                item = category.pop(0)
                feed = category
                idr = '%s:%s@facebook/feed#%s'%(item['type'],service_user.userid, item['id'])
                data_type = 'FEED'
            elif category == inbox:
                item = category.pop(0)
                inbox = category
                idr = 'inbox:%s@facebook/inbox#%s'%(service_user.userid, item['id'])
                data_type = 'INBOX'
                data.append(item)
            elif category == photos:
                item = category.pop(0)
                photos = category
                idr = 'photo:%s@facebook/photos#%s'%(service_user.userid, item['id'])
                data_type = 'PHOTO'
            elif category == home:
                item = category.pop(0)
                home = category
                idr = '%s:%s@facebook/home#%s'%(item['type'],service_user.userid, item['id'])
                data_type = 'HOME'
            #elif category == notes:
                #item = category.pop(0)
                #notes = category
                #idr = 'note:%s@facebook/notes#%s'%(service_user.userid, item['id'])
                #data_type = 'NOTE'
            elif category == links:
                item = category.pop(0)
                links = category
                idr = 'link:%s@facebook/links#%s'%(service_user.userid, item['id'])
                data_type = 'LINK'
            elif category == statuses:
                item = category.pop(0)
                statuses = category
                idr = 'status:%s@facebook/statuses#%s'%(service_user.userid, item['id'])
                data_type = 'STATUS'
            elif category == posts:
                item = category.pop(0)
                posts = category
                idr = 'post:%s@facebook/posts#%s'%(service_user.userid, item['id'])
                data_type = 'POST'
            elif category == friends:
                item = category.pop(0)
                friends = category
                idr = 'friend:%s@facebook/friends#%s'%(service_user.userid, item['id'])
                data_type = 'FRIEND'
            elif category == groups:
                item = category.pop(0)
                groups = category
                idr = 'group:%s@facebook/groups#%s'%(service_user.userid, item['id'])
                data_type = 'GROUP'
            elif category == albums:
                item = category.pop(0)
                albums = category
                idr = 'album:%s@facebook/albums#%s'%(service_user.userid, item['id'])
                data_type = 'ALBUM'
            if len(category) > 0:
                queue.append(category)
        if item:
            try:
                facebook_id = FacebookData.objects.get(idr=idr)
            except FacebookData.DoesNotExist:
                facebook_id = FacebookData(idr=idr, data=item, neemiuser=currentuser.id, facebook_user=service_user, data_type=data_type,
                        time=datetime.today()).save()
                count += 1
            data.append(item)
    print "%d new Facebook items added"%count
    return data



def get_inbox(fromtimestamp, totimestamp, access_token):
    fields = 'id,comments,to,unread,unseen,updated_time'
    #sinceTime = datetime(2013, 01, 01, 00, 00, 01)
    url = 'https://graph.facebook.com/me/inbox?limit=1000&access_token=%s'%access_token
    #if fromtimestamp is not None:
    #       url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    url += '&fields=%s'%fields
    print url

    inbox=json.load(urllib2.urlopen(url))

    returnData = []
    while True:

        try:
            returnData = returnData + [ x for x in inbox['data']]
            print "URL= ", inbox['paging']['next']
            inbox = json.load(urllib2.urlopen(inbox['paging']['next']))
        except:
            break

    return returnData


def get_events(fromtimestamp, totimestamp, access_token):
    fields = 'description,id,end_time,location,name,owner,rsvp_status,start_time,venue'
    url = 'https://graph.facebook.com/me/events?limit=1000&access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    url += '&fields=%s'%fields
    print url

    events=json.load(urllib2.urlopen(url))

    returnData = []
    while True:

        try:
            returnData = returnData + [ x for x in events['data']]
            events = json.load(urllib2.urlopen(events['paging']['next']))
        except:
            break
    return returnData


def get_standard_data(field, fromtimestamp, totimestamp, access_token):
    if field=='home':
        url = 'https://graph.facebook.com/me/home?limit=1000&filter=owner&access_token=%s'%access_token
        #if fromtimestamp is not None:
        #    url += '&since=%s'%fromtimestamp
        #url += '&until=%s'%totimestamp
        print url

        standard_data=json.load(urllib2.urlopen(url))

        returnData = []

        while True:
            try:

                returnData = returnData + [ x for x in standard_data['data']]
                print "URL= ", standard_data['paging']['next']
                standard_data = json.load(urllib2.urlopen(standard_data['paging']['next']))
            except:
                break
        url = 'https://graph.facebook.com/me/home?limit=1000&filter=others&access_token=%s'%access_token
        #if fromtimestamp is not None:
        #    url += '&since=%s'%fromtimestamp
        #url += '&until=%s'%totimestamp
        print url

        standard_data=json.load(urllib2.urlopen(url))

        while True:
            try:

                returnData = returnData + [ x for x in standard_data['data']]
                print "URL= ", standard_data['paging']['next']
                standard_data = json.load(urllib2.urlopen(standard_data['paging']['next']))
            except:
                break
    else:
        url = 'https://graph.facebook.com/me/%s?limit=1000&access_token=%s'%(field, access_token)
        #if fromtimestamp is not None:
        #    url += '&since=%s'%fromtimestamp
        #url += '&until=%s'%totimestamp
        print url

        standard_data=json.load(urllib2.urlopen(url))

        returnData = []
        while True:

            try:
                returnData = returnData + [ x for x in standard_data['data']]
                print "URL= ", standard_data['paging']['next']
                standard_data = json.load(urllib2.urlopen(standard_data['paging']['next']))
            except:
                break

    return returnData

def get_user_wall (fromtimestamp, totimestamp, access_token):

    url = 'https://graph.facebook.com/me/feed?limit=1000&access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    print url

    user_feeds = json.load(urllib2.urlopen(url))
    Data = []
    while True :
        try:
            Data = Data + user_feeds['data']
            user_feeds = json.load(urllib.urlopen(user_feeds['paging']['next']))
            #max_pages = max_pages-1
            #if max_pages < 1 :
            #       break
        except:
            break
    return Data

def get_photos(fromtimestamp, totimestamp, access_token):
    photos = []
    fields = 'album,from,id,name,created_time,name_tags,place,source,link,updated_time,tags'
    url = 'https://graph.facebook.com/me/photos?limit=1000&access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    url += '&fields=%s'%fields
    url += '&type=tagged'
    print url

    f = urllib2.urlopen(url)
    json_string = f.read()
    for photo in loads(json_string)['data']:
        photos.append(photo)

    url = url[0:(len(url)-len('tagged'))]
    url += 'uploaded'
    print url

    f.close()
    f = urllib2.urlopen(url)
    json_string = f.read()
    for photo in loads(json_string)['data']:
        photos.append(photo)
    f.close()
    return photos



def get_friends(access_token):
    #maxPage=4
    #friends = json.load(urllib2.urlopen('https://graph.facebook.com/me/friends?limit=1000&access_token=%s'%access_token))
    #Friends = []
    #while "next" in friends["paging"]:
    #       if maxPage == 0:
    #               break
    #       maxPage = maxPage - 1
    #       Friends = Friends + friends["data"]
    #       friends = json.load(urllib2.urlopen(friends["paging"]["next"]))
    #return Friends
    friends = []
    url = 'https://graph.facebook.com/me/friends?limit=1000&access_token=%s'%access_token
    print url

    f = urllib2.urlopen(url)
    json_string = f.read()
    for friend in loads(json_string)['data']:
        url = 'https://graph.facebook.com/%s?limit=1000&access_token=%s'%(friend['id'], access_token)
        f.close()
        f = urllib2.urlopen(url)
        json_string_2 = f.read()
        friends.append(loads(json_string_2))
    f.close()
    return friends

def get_groups(access_token):

    groups = []
    url = 'https://graph.facebook.com/me/groups?limit=1000&access_token=%s'%access_token
    print url

    f = urllib2.urlopen(url)
    json_string = f.read()
    for group in loads(json_string)['data']:
        url = 'https://graph.facebook.com/%s?access_token=%s'%(group['id'], access_token)
        f.close()
        f = urllib2.urlopen(url)
        json_string_2 = f.read()
        groups.append(loads(json_string_2))
    f.close()
    return groups
