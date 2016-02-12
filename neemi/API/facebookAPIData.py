from neemi.models import *
import urllib2
import json
from bson.json_util import loads
import datetime

from time import mktime
import calendar
from operator import *


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
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
        totimestamp = datetime.datetime.today().strftime('%s')

    print "fromtimestamp: ", fromtimestamp
    print "totimestamp: ", totimestamp

    data = []
    latestFirst = True
    if fromtimestamp is not None:
        latestFirst = False
        print 'Getting news feed....'
    #home=[]
    print "Getting home...."
    home = get_standard_data('home', fromtimestamp, totimestamp,request.get('access_token'))
    try:
        home.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting tagged places...."
    tagged_places = get_tagged_places(fromtimestamp, totimestamp, request.get('access_token'))
    print "Getting events...."
    events = get_events(fromtimestamp, totimestamp, request.get('access_token'))
    try:
        events.sort(key=itemgetter('start_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting inbox threads...."
    inbox = get_inbox(fromtimestamp, totimestamp, request.get('access_token'))
    print "Getting inbox all messages"
    inbox_messages=[]
    #inbox_messages = get_inbox_messages(inbox, fromtimestamp, totimestamp, request.get('access_token'))
    print "Getting user's wall...."
    #feed=[]
    feed = get_user_wall(fromtimestamp, totimestamp, request.get('access_token'))
    try:
        feed.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting photos...."
    photos = get_photos(fromtimestamp, totimestamp, request.get('access_token'))
    try:
        photos.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting statuses...."
    statuses = get_standard_data('statuses', fromtimestamp, totimestamp, request.get('access_token'))
    try:
        statuses.sort(key=itemgetter('updated_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting links...."
    links = get_standard_data('links', fromtimestamp, totimestamp, request.get('access_token'))
    try:
        links.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting posts...."
    posts = get_standard_data('posts', fromtimestamp, totimestamp, request.get('access_token'))
    try:
        posts.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    print "Getting friends...."
    friends = get_friends(fromtimestamp, totimestamp, request.get('access_token'))
    print "Getting groups...."
    groups = get_groups(fromtimestamp, totimestamp, request.get('access_token'))
    print "Getting albums...."
    albums = get_standard_data('albums', fromtimestamp, totimestamp, request.get('access_token'))
    try:
        albums.sort(key=itemgetter('created_time'), reverse=latestFirst)
    except Exception as e:
        pass
    

    data = process_data(request=request, currentuser=currentuser, service_user=service_user, data=data, events=events, feed=feed,
            photos=photos, home=home, statuses=statuses, links=links, posts=posts, friends=friends, groups=groups, albums=albums, inbox=inbox, tagged_places=tagged_places, inbox_messages=inbox_messages)

    return data
        

def process_data(request, currentuser, service_user, data, events, feed, photos, home, statuses, links, posts, friends, groups, albums, inbox, tagged_places, inbox_messages):
    print 'Process Facebook data'
    queue = []
    queue.append(events)
    queue.append(feed)
    queue.append(photos)
    queue.append(home)
    queue.append(links)
    queue.append(statuses)
    queue.append(posts)
    queue.append(friends)
    queue.append(groups)
    queue.append(albums)
    queue.append(inbox)
    queue.append(inbox_messages)
    queue.append(tagged_places)


    count = 0
    counter=0
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
                print 'Process Events'
            elif category == feed:
                item = category.pop(0)
                feed = category
                idr = '%s:%s@facebook/feed#%s'%(item['type'],service_user.userid, item['id'])
                data_type = 'FEED'
                print 'Process Feeds'
            elif category == inbox:
                item = category.pop(0)
                inbox = category
                idr = 'inbox:%s@facebook/inbox#%s'%(service_user.userid, item['id'])
                data_type = 'INBOX'
                print 'Process Inbox'
            elif category == inbox_messages:
                item = category.pop(0)
                inbox_messages = category
                idr = 'inbox_messages:%s@facebook/inbox_messages#%s'%(service_user.userid, item['id'])
                data_type = 'INBOX_MSG'
                print 'Process Inbox messages'
            elif category == photos:
                item = category.pop(0)
                photos = category
                idr = 'photo:%s@facebook/photos#%s'%(service_user.userid, item['id'])
                data_type = 'PHOTO'
                print 'Process Photos'
            elif category == home:
                item = category.pop(0)
                home = category
                idr = '%s:%s@facebook/home#%s'%(item['type'],service_user.userid, item['id'])
                data_type = 'HOME'
                print 'Process Home'
            elif category == tagged_places:
                item = category.pop(0)
                tagged_places = category
                idr = '%s:%s@facebook/tagged_places#%s'%(service_user.userid, item['id'])
                data_type = 'TAGGED_PLACES'
                print 'Process tagged_places'
            elif category == links:
                item = category.pop(0)
                links = category
                idr = 'link:%s@facebook/links#%s'%(service_user.userid, item['id'])
                data_type = 'LINK'
                print 'Process Links'
            elif category == statuses:
                item = category.pop(0)
                statuses = category
                idr = 'status:%s@facebook/statuses#%s'%(service_user.userid, item['id'])
                data_type = 'STATUS'
                print 'Process Statuses'
            elif category == posts:
                item = category.pop(0)
                posts = category
                idr = 'post:%s@facebook/posts#%s'%(service_user.userid, item['id'])
                data_type = 'POST'
                print 'Process Posts'
            elif category == friends:
                item = category.pop(0)
                friends = category
                idr = 'friend:%s@facebook/friends#%s'%(service_user.userid, item['id'])
                data_type = 'FRIEND'
                print 'Process Friends'
            elif category == groups:
                item = category.pop(0)
                groups = category
                idr = 'group:%s@facebook/groups#%s'%(service_user.userid, item['id'])
                data_type = 'GROUP'
                print 'Process Groups'
            elif category == albums:
                item = category.pop(0)
                albums = category
                idr = 'album:%s@facebook/albums#%s'%(service_user.userid, item['id'])
                data_type = 'ALBUM'
                print 'Process Albums'
            if len(category) > 0:
                queue.append(category)
        if item:
            try:
                facebook_id = FacebookData.objects.get(idr=idr)
            except FacebookData.DoesNotExist:
                facebook_id = FacebookData(idr=idr, data=item, neemiuser=currentuser.id, facebook_user=service_user, data_type=data_type,
                        time=datetime.datetime.today()).save()
                count += 1
            data.append(item)
    print "%d new Facebook items added"%count
    return data


def get_tagged_places(fromtimestamp, totimestamp, access_token):
    #sinceTime = datetime(2013, 01, 01, 00, 00, 01)
    url = 'https://graph.facebook.com/me/tagged_places?access_token=%s'%access_token
    #if fromtimestamp is not None:
    #       url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    print url

    get_tagged_places=json.load(urllib2.urlopen(url))

    returnData = []
    while True:

        try:
            returnData = returnData + [ x for x in get_tagged_places['data']]
            print "URL= ", get_tagged_places['paging']['next']
            get_tagged_places = json.load(urllib2.urlopen(get_tagged_places['paging']['next']))
        except:
            break

    return returnData

def get_inbox_messages(inbox, fromtimestamp, totimestamp, access_token):

	messages=[]
	for thread in inbox:
		url = thread['comments']['paging']['next']
		print url
		thread = json.load(urllib2.urlopen(thread['comments']['paging']['next']))
		
		while True:
			try:
				messages = messages + thread
				print 'URL1= ', thread['paging']['next']
				thread = json.load(urllib2.urlopen(thread['paging']['next']))
			except Exception, excpt:
				break
	return messages
		

def get_inbox(fromtimestamp, totimestamp, access_token):

    # fields = 'id,comments,to,unread,unseen,updated_time'
    # sinceTime = datetime(2013, 01, 01, 00, 00, 01)

    url = 'https://graph.facebook.com/me/inbox?access_token=%s'% access_token

    # if fromtimestamp is not None:
     #      url += '&since=%s'%fromtimestamp
    # url += '&until=%s'%totimestamp
    # url += '&fields=%s'%fields

    print url

    inbox = json.load(urllib2.urlopen(url))

    returnData = []
	
    while True:
        try:
            returnData = returnData + inbox['data']
            print 'URL1= ', inbox['paging']['next']
            inbox = json.load(urllib2.urlopen(inbox['paging']['next']))
        except Exception, excpt:
            break
    return returnData

    returnData = []
    returnData = returnData + messages	
    while True:
        try:
            returnData = returnData + inbox['data']
            print 'URL1= ', inbox['paging']['next']
            inbox = json.load(urllib2.urlopen(inbox['paging']['next']))
        except Exception, excpt:
            break

    return returnData



def get_events(fromtimestamp, totimestamp, access_token):
    fields = 'description,id,end_time,name,owner,rsvp_status,start_time' #location, venue
    url = 'https://graph.facebook.com/me/events?access_token=%s'%access_token
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
		oneDayAgo = datetime.datetime.today() - datetime.timedelta(1)
		print "two days ago= ", oneDayAgo
		fromtimestamp = oneDayAgo.strftime('%s')
		

		url = 'https://graph.facebook.com/me/home?access_token=%s'%access_token
		#if fromtimestamp is not None:
		#	url += '&since=%s'%fromtimestamp
		#url += '&until=%s'%totimestamp
		print url

		standard_data=json.load(urllib2.urlopen(url))
					
		#returnData = standard_data['data']
		returnData = []
		max_pages=100

		
		while True :
			try:
				returnData = returnData + standard_data["data"]
				print "URL= ", standard_data['paging']['next']
				standard_data = json.load(urllib2.urlopen(standard_data["paging"]["next"]))
				max_pages = max_pages-1
				if max_pages < 1 :
					print "It is less than 1"
					break
			except Exception as e:
				print "Exception = ", e
				break
       				
        		
		#while True:
		#	try:
		#		returnData = returnData + [ x for x in standard_data['data']]
		#		print "URL= ", standard_data['paging']['next']
		#		standard_data = json.load(urllib2.urlopen(standard_data['paging']['next']))
		#		print "Size of subsequent calls = ", len(standard_data['data'])	

		#	except:
		#		break
    else:
        url = 'https://graph.facebook.com/me/%s?access_token=%s'%(field, access_token)
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

    url = 'https://graph.facebook.com/me/feed?access_token=%s'%access_token
    #if fromtimestamp is not None:
    #   url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    print url

    user_feeds = json.load(urllib2.urlopen(url))
    Data = []
    
    while True :
        try:
            Data = Data + user_feeds['data']
            print "URL= ", user_feeds['paging']['next']
            user_feeds = json.load(urllib2.urlopen(user_feeds['paging']['next']))
        except Exception as e:
        	break
    return Data

def get_photos(fromtimestamp, totimestamp, access_token):
    #photos = []   
    
    fields = 'album,from,id,name,created_time,name_tags,place,source,link,updated_time,tags'
    url = 'https://graph.facebook.com/me/photos?access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    url += '&fields=%s'%fields
    #url += '&type=tagged'
    print url

    photos=json.load(urllib2.urlopen(url))

    returnData = []
    while True:
        try:
            returnData = returnData + [ x for x in photos['data']]
            photos = json.load(urllib2.urlopen(photos['paging']['next']))
        except:
            break
    return returnData




def get_friends(fromtimestamp, totimestamp, access_token):
    #maxPage=4
    #friends = json.load(urllib2.urlopen('https://graph.facebook.com/me/friends?access_token=%s'%access_token))
    #Friends = []
    #while "next" in friends["paging"]:
    #       if maxPage == 0:
    #               break
    #       maxPage = maxPage - 1
    #       Friends = Friends + friends["data"]
    #       friends = json.load(urllib2.urlopen(friends["paging"]["next"]))
    #return Friends
    friends = []
    url = 'https://graph.facebook.com/me/friends?access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
    print url

    friends=json.load(urllib2.urlopen(url))

    returnData = []
    #for summary in friends['summary']:
    #    returnData.append(summary)
    #print returnData    
    #while True:
    #    try:
    #        returnData = returnData + [ x for x in friends['data']]
    #        friends = json.load(urllib2.urlopen(friends['paging']['next']))
    #    except:
    #        break
            
    return returnData

def get_groups(fromtimestamp, totimestamp, access_token):

    groups = []
    url = 'https://graph.facebook.com/me/groups?access_token=%s'%access_token
    #if fromtimestamp is not None:
    #    url += '&since=%s'%fromtimestamp
    #url += '&until=%s'%totimestamp
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
