import time,datetime
import os

# Handles JSON across multiple Python versions
try: import simplejson as json
except ImportError: import json

from neemi.models import *
from googleAPI import GoogleHelper

import gdata

from oauth2client import client
import imaplib
import email

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

import requests
import json


def timestamp():
    now = time.time()
    localtime = time.localtime(now)
    milliseconds = '%03d' % int((now - int(now)) * 1000)
    return time.strftime('%Y%m%d%H%M%S', localtime) + milliseconds

def remove_dots_key(obj):
    for key in obj.keys():
        new_key = key.replace(".","_")
        if new_key != key:
            obj[new_key] = obj[key]
            del obj[key]
    return obj

def convert2unicode(obj):
    obj = unicode(obj, errors = 'replace')
    return obj

def try_utf8(data):
    "Returns a Unicode object on success, or None on failure"
    valid_utf8 = True
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        print "False"
        valid_utf8 = False
        #pass

    return valid_utf8

class MyError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class GoogleAPIData(object):

    def getGoogleProfile(self, request={}):
        print "Get Profile Data from google"           
        currentuser = User.objects.get(username=request.user.username)
        service_user = GoogleUser.objects.get(neemi_user=currentuser)           
        print [service_user]
        print "done google profile"
        return service_user

    def getGoogleData(self, request={}, service=None):
        currentuser = User.objects.get(username=request.user.username)

        service_user = GoogleUser.objects.get(neemi_user=currentuser)

        print "Service_user: ", service_user

        client = GoogleHelper.create_google_client(service=service, user=service_user)

        print "Client: ", client
        print "service_user.last_calendar_access: ", service_user.last_calendar_access
        print "service_user.last_email_access: ", service_user.last_email_access
        print "service_user.last_contacts_access: ", service_user.last_contacts_access

        if service == 'gcal':
            gcal = gcalData(client=client, user=service_user)
            gcal.getALLCalendarsMetadata()
            gcal.getALLCalendarsEvents()

            # update date that the calendar was last accessed
            service_user.last_calendar_access = datetime.datetime.now()
            service_user.save()
        if service == 'googleplus':
            gplus = gplusData(client=client, user=service_user)
            # get activities and comments
            #gplus.getActivities()
            gplus.getALLActivities()
        if service == 'gmail':
            gmail = gmailData(client=client, user=service_user)
            #gmail.getUnseenEmails()
            #gmail.printMailBoxes()
            gmail.getALLInbox()
            gmail.getALLSentEmails()
	    #gmail.getALLMail()
            # update date that the email was last accessed
            service_user.last_email_access = datetime.date.today()
            service_user.save()
            print "DONE collecting emails"
        if service == 'googlecontacts':
            gcontacts = gcontactsData(client=client, user=service_user)
            if (service_user.last_contacts_access == None):
                print "List all contacts: "
                gcontacts.ListAllContacts()
            else:
                print "List contacts updated since ", service_user.last_contacts_access
                gcontacts.ListContactsUpdatedSince()
            service_user.last_contacts_access = str(datetime.date.today())
            service_user.save()
            #gcontacts.ListAllGroups()


class gcontactsData(object):

    def __init__(self, client=None, user=None):
        self.client = client
        self.user = user

    def ListContactsUpdatedSince(self):
        from_date = self.user.last_contacts_access
        query = gdata.contacts.client.ContactsQuery()
        query.updated_min = from_date
        feed = self.client.GetContacts(q=query)
        print '===> Number of entries: ', len(feed.entry)
        self.PrintPaginatedFeed(feed, self.PrintContactsFeed)
        print "Done listing all contacts updated sice last call!!"

    def ListAllContacts(self):
        """Retrieves a list of contacts and displays name and primary email."""
        feed = self.client.GetContacts()
        print '===> Number of entries: ', len(feed.entry)
        self.PrintPaginatedFeed(feed, self.PrintContactsFeed)
        print "Done listing all contacts!!"        
        

    def PrintContactsFeedOLD(self, feed, ctr):
        print 'Printing feeds...'
        if not feed.entry:
            print '\nNo contacts in feed.\n'
            return 0

        for i, entry in enumerate(feed.entry):
            response = []
          
            response.append({'id':entry.id.text})
            if not entry.name is None:
                family_name = entry.name.family_name is None and " " or entry.name.family_name.text
                full_name = entry.name.full_name is None and " " or entry.name.full_name.text
                given_name = entry.name.given_name is None and " " or entry.name.given_name.text
                response.append({'name': full_name})
            else:
                response.append({'title': entry.title.text})
            if entry.content:
                response.append({'content': entry.content.text})
            for email in entry.email:
                if email.primary and email.primary == 'true':
                    response.append({'email address': email.address})
            count = 0
            for p in entry.structured_postal_address:
                count = count + 1
                addr = 'address %s' % count
                response.append({addr: p.formatted_address.text})

            # Display the group id which can be used to query the contacts feed.
            response.append({'group id': entry.id.text})

            if not entry.updated is None:
                response.append({'updated': entry.updated.text})

            service_data, created = GcontactsData.objects.get_or_create(feed_id=entry.id.text,neemi_user=self.user.neemi_user)
            service_data.gcontacts_user = self.user
            service_data.data = json.dumps(response)
            if not entry.updated is None:
                service_data.time = entry.updated.text
            else:
                service_data.time = datetime.datetime.now()
            service_data.data_type = 'CONTACT' 
            service_data.save()             

        return len(feed.entry) + ctr

    def PrintContactsFeed(self, feed, ctr):
        print 'Printing feeds...'
        if not feed.entry:
            print '\nNo contacts in feed.\n'
            return 0

        for i, entry in enumerate(feed.entry):
            response = {}
          
            response['id'] = entry.id.text
            if not entry.name is None:
                family_name = entry.name.family_name is None and " " or entry.name.family_name.text
                full_name = entry.name.full_name is None and " " or entry.name.full_name.text
                given_name = entry.name.given_name is None and " " or entry.name.given_name.text
                response['name'] = full_name
            else:
                response['title'] = entry.title.text
            if entry.content:
                response['content'] = entry.content.text
            for email in entry.email:
                if email.primary and email.primary == 'true':
                    response['email_address'] = email.address
            count = 0
            for p in entry.structured_postal_address:
                count = count + 1
                addr = 'address %s' % count
                response['addr'] = p.formatted_address.text

            # Display the group id which can be used to query the contacts feed.
            response['group_id'] = entry.id.text

            if not entry.updated is None:
                response['updated'] = entry.updated.text

            service_data, created = GcontactsData.objects.get_or_create(feed_id=entry.id.text,neemi_user=self.user.neemi_user)
            service_data.gcontacts_user = self.user
            service_data.data = json.dumps(response)
            if not entry.updated is None:
                service_data.time = entry.updated.text
            else:
                service_data.time = datetime.datetime.now()
            service_data.data_type = 'CONTACT' 
            service_data.save()             

        return len(feed.entry) + ctr

    def ListAllGroups(self):
        feed = self.client.GetGroups()
        self.PrintPaginatedFeed(feed, self.PrintGroupsFeed)

    def PrintGroupsFeed(self, feed, ctr):
        if not feed.entry:
            print '\nNo groups in feed.\n'
            return 0
        for i, entry in enumerate(feed.entry):
            print '\n%s %s' % (ctr+i+1, entry.title.text)
            if entry.content:
                print '    %s' % (entry.content.text)
            # Display the group id which can be used to query the contacts feed.
            print '    Group ID: %s' % entry.id.text
            # Display extended properties.
            for extended_property in entry.extended_property:
                if extended_property.value:
                    value = extended_property.value
                else:
                    value = extended_property.GetXmlBlob()
                print '    Extended Property %s: %s' % (extended_property.name, value)
        return len(feed.entry) + ctr


    def PrintPaginatedFeed(self, feed, print_method):
        """  
        This will iterate through a paginated feed, requesting each page and
        printing the entries contained therein.
   
        Args:
        feed: A gdata.contacts.ContactsFeed instance.
        print_method: The method which will be used to print(store) each page of the feed. 
        Must accept these two named arguments:
              feed: A gdata.contacts.ContactsFeed instance.
              ctr: [int] The number of entries in this feed previously
                  printed. This allows continuous entry numbers when paging
                  through a feed.
        """
        ctr = 0
        while feed:
            # Print contents of current feed
            ctr = print_method(feed=feed, ctr=ctr)
            # Prepare for next feed iteration
            next = feed.GetNextLink()
            feed = None
            if next:
                # Another feed is available, and the user has given us permission
                # to fetch it
                feed = self.client.GetContacts(next.href)



class gcalData(object):

#TODO: I am not sure how to use the updatedMin parameter
#        timeMin=datetime.datetime.fromtimestamp(int(from_date)/1000).isoformat('T') + 'Z'
#        delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(int(from_date)/1000)
#        print [delta]
#        if delta.days<25:
#            gcal_request['updatedMin'] = timeMin
#            gcal_request['orderBy']='updated'
#        else:
#            gcal_request['timeMin'] = timeMin
#            gcal_request['orderBy']='startTime'

    def __init__(self, client=None, user=None):
        self.client = client
        self.ids = self.getUserCalendarList()
        self.user = user
        print "Calendar ids: ", self.ids


    # Get list of all calendars from an user
    def getUserCalendarList(self):
        calendar_ids = []
        print "Getting list of user's calendars..."
        request = self.client.calendarList().list()
        if request != None:
            calendars = request.execute()
            if 'items' in calendars and calendars['items']!=None:
                calendars = calendars['items'] 
                for item in calendars:
                    calendar_ids.append(item['id']) 
        return calendar_ids 


    def getCalendarMetadata(self, calId=None):
        request = self.client.calendars().get(calendarId=calId)
        if request != None:
            response = request.execute()

            print 
            print "===> Metadata: ", response
            print

            self.storeMetadata(data=response)  


    def getALLCalendarsMetadata(self):
        print "Getting calendar metadata..."
        for i in range(0, len(self.ids)):
            self.getCalendarMetadata(calId=self.ids[i])   


    def getCalendarEvents(self, calId=None):
        print "Getting events: ", calId

        from_date = self.user.last_calendar_access

        # The Calendar API's events().list method returns paginated results, so we
        # have to execute the request in a paging loop. First, build the request
        # object. The arguments provided are:
        #   calendar id
        #   event's start time
        if (from_date == None):
            request = self.client.events().list(calendarId=calId)
        else:
            print "from_date(1): ", from_date
            from_date = int(time.mktime(from_date.timetuple()))//1*1000
            print "from_date(2): ", from_date
            timeMin = datetime.datetime.fromtimestamp(int(from_date)/1000).isoformat('T') + 'Z'
            print "timeMin: ", timeMin
            request = self.client.events().list(calendarId=calId, timeMin=timeMin)
            #request = self.client.events().list(calendarId=calId, timeMin=timeMin, orderBy='startTime')

        # Loop until all pages have been processed.
        while request != None:
            # Get the next page.
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (events).
            for event in response.get('items', []):
                # The event object is a dict object with a 'summary' key.
                print "Event: ", event
                self.storeEvent(data=event, calendarId=calId)
          
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = self.client.events().list_next(request, response)

    
    def getALLCalendarsEvents(self):
        print "Getting events..."
        for i in range(0, len(self.ids)):
            self.getCalendarEvents(calId=self.ids[i])  


    def storeEvent(self, data=None, calendarId=None):
        service_data, created = GcalData.objects.get_or_create(event_id=data['id'],neemi_user=self.user.neemi_user)
        service_data.gcal_user = self.user
        # Some events have keys with dots. Those have to be replaced before the data can be stored in MongoDB.
        new_data = json.loads(json.dumps(data), object_hook=remove_dots_key) 
        service_data.data = new_data  
        service_data.calendar_id = calendarId 
        #TODO: time was not being used during singly implementation. If we decide to use that we wil have to deal with the RFC 3339 format and convert it to a standard python timestamp
        # Consider: http://code.google.com/p/feedparser/
        # data when event was created  
        #service_data.time = data['created']
        service_data.data_type = 'EVENT' 
        service_data.save() 

    def storeMetadata(self, data=None):        
        service_data, created = GcalData.objects.get_or_create(calendar_id=data['id'],data_type='METADATA',neemi_user=self.user.neemi_user)
        if created:
            service_data.gcal_user = self.user
        # if calendar already exist, update data.  
        service_data.data = data
        # For calendar metadata, event_id and time do not exist
        #service_data.event_id = ''  
        #service_data.time = ''  
        service_data.save() 


class gplusData():

    def __init__(self, client=None, user=None):
        self.client = client
        self.user = user
        self.people_ids = self.getPeople()

    def getPeople(self):
        people_ids = []

        request = self.client.people().list(userId='me', collection='visible')
        # Loop until all pages have been processed.
        while request != None:
            # Get the next page.
	    
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (people).
            for item in response.get('items', []):
                #self.storePeople(data=item)
                self.storeData(data=item, data_type='PEOPLE')
                people_ids.append(item['id'])
          
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = self.client.people().list_next(request, response)
        return people_ids
    
    def storePeople(self, data=None): 
        # For people, the id is the user_id       
        service_data, created = GplusData.objects.get_or_create(id=data['id'],neemi_user=self.user.neemi_user)
        if created:
            service_data.gplus_user = self.user
            service_data.data_type = 'PEOPLE'
        # if person already exist, update data.  
        service_data.data = data 
        service_data.save() 


    def getActivities(self, userId=None):
        request = self.client.activities().list(userId=userId, collection='public')
        # Loop until all pages have been processed.
        while request != None:
            # Get the next page.
            jrequest = request.to_json()    
            print "Request: ", jrequest
            response = request.execute()
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (activities).
            for item in response.get('items', []):
                self.storeData(data=item, data_type='ACTIVITIES')
                # For each activity, retrieve a list of comments
                self.getComments(activityId=item['id'])
          
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = self.client.activities().list_next(request, response)
    
    def getALLActivities(self):
        print "Getting activities..."
        for i in range(0, len(self.people_ids)):
            self.getActivities(userId=self.people_ids[i]) 

    def getComments(self, activityId=None):
        request = self.client.comments().list(activityId=activityId)
        # Loop until all pages have been processed.
        while request != None:
            # Get the next page.
            response = request.execute()
#            print "Response: ", response
            # Accessing the response like a dict object with an 'items' key
            # returns a list of item objects (comments).
            for item in response.get('items', []):
                self.storeData(data=item, data_type='COMMENTS')
          
            # Get the next request object by passing the previous request object to
            # the list_next method.
            request = self.client.comments().list_next(request, response)


    def storeData(self, data=None, data_type=None): 
        # For people, the id is the user_id 
        # For activities, the id is the activity id   
        # For comments, the is is the comment id 
        service_data, created = GplusData.objects.get_or_create(feed_id=data['id'],neemi_user=self.user.neemi_user)
        if created:
            service_data.gplus_user = self.user
            service_data.data_type = data_type
            if (data_type == 'PEOPLE'):
                service_data.time = datetime.datetime.now()
            else:
                service_data.time = data['published']
        # if person already exist, update data.  
        service_data.data = data 
        service_data.save() 


class gmailData():

    def __init__(self, client=None, user=None):
        self.client = client
        self.user = user


    def getUnseenEmails(self):
        # Search for all new mail
        self.client.select()
        status, email_ids = self.client.search(None, '(UNSEEN)')

    
    def getALLInbox(self):
        self.client.select('INBOX', readonly=True)

        if (self.user.last_email_access == None):
            status, data = self.client.search(None, 'ALL')
        else:
            date = (self.user.last_email_access - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, data = self.client.search(None, '(SENTSINCE {date})'.format(date=date))
        ids = data[0]

        if not ids:
            print "No new messages!"
            return

        id_list = ids.split()

        for i in id_list:
            try:
                status, data = self.client.fetch( i, '(RFC822)' )
                self.storeEmail(emailId=i, data_type='INBOX', data=data)
            except MyError as e:
                print 'Could not add email - ', e
                continue 


        self.client.close() 

        print "List of ids: ", len(id_list)      


    def getInbox(self):
        MAX = 200
        self.client.select('INBOX', readonly=True)

        if (self.user.last_email_access == None):
            status, data = self.client.search(None, 'ALL')
        else:
            date = (self.user.last_email_access - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, data = self.client.search(None, '(SENTSINCE {date})'.format(date=date))
        ids = data[0]

        if not ids:
            print "No new messages!"
            return

        id_list = ids.split()
        #get the most recent email id
        latest_email_id = int( id_list[-1] )

        if (latest_email_id-MAX > 0):
            numberOfmsg = latest_email_id-MAX
        else:
            numberOfmsg = id_list[0]

        #iterate through MAX messages in decending order starting with latest_email_id
        #the '-1' dictates reverse looping order
        for i in range( latest_email_id, numberOfmsg, -1 ):
            try:
                status, data = self.client.fetch( i, '(RFC822)' )
                self.storeEmail(emailId=i, data_type='INBOX', data=data)
            except Exception as e:
                print 'Could not add email - ', e
                print data
                continue 

        self.client.close()

        
    def printMailBoxes(self):
        mailboxes = []
        rc, response = self.client.list()
        for item in response:
            mailboxes.append(item.split()[-1])
        for item in mailboxes:
            print item
    
    def getALLMail(self):
        self.client.select('[Gmail]/All Mail', readonly=True)

        if (self.user.last_email_access == None):
            status, data = self.client.search(None, 'ALL')
        else:
            date = (self.user.last_email_access - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, data = self.client.search(None, '(SENTSINCE {date})'.format(date=date))
        ids = data[0]

        if not ids:
            print "No new messages!"
            return

        id_list = ids.split()

        for i in id_list:
            try:
                status, data = self.client.fetch( i, '(RFC822)' )
                self.storeEmail(emailId=i, data_type='ALL_MAIL', data=data)
            except Exception as e:
                print 'Could not add email - ', e
                continue 
        self.client.close() 

        print "List of ids: ", len(id_list) 

    def getALLSentEmails(self):

        self.client.select('[Gmail]/Sent Mail')
        if (self.user.last_email_access == None):
            status, data = self.client.search(None, 'ALL')
        else:
            date = (self.user.last_email_access - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, data = self.client.search(None, '(SENTSINCE {date})'.format(date=date))
        ids = data[0]

        if not ids:
            print "No new messages!"
            return

        id_list = ids.split()

        for i in id_list:
            try:
                status, data = self.client.fetch( i, '(RFC822)' )
                self.storeEmail(emailId=i, data_type='SENT', data=data)
            except Exception as e:
                print 'Could not add email - ', e
                print data

        self.client.close()

        print "List of ids: ", len(id_list)  



    def getSentEmails(self):
        MAX = 200

        self.client.select('[Gmail]/Sent Mail')
        if (self.user.last_email_access == None):
            status, data = self.client.search(None, 'ALL')
        else:
            date = (self.user.last_email_access - datetime.timedelta(1)).strftime("%d-%b-%Y")
            status, data = self.client.search(None, '(SENTSINCE {date})'.format(date=date))
        ids = data[0]

        if not ids:
            print "No new messages!"
            return

        id_list = ids.split()
        #get the most recent email id
        latest_email_id = int( id_list[-1] )

        if (latest_email_id-MAX > 0):
            numberOfmsg = latest_email_id-MAX
        else:
            numberOfmsg = id_list[0]

        #iterate through MAX messages in decending order starting with latest_email_id
        #the '-1' dictates reverse looping order
        for i in range( latest_email_id, numberOfmsg, -1 ):
            try:
                status, data = self.client.fetch( i, '(RFC822)' )
                self.storeEmail(emailId=i, data_type='SENT', data=data)
            except Exception as e:
                print 'Could not add email - ', e
                print data

        self.client.close()


#        #iterate through MAX messages in decending order starting with latest_email_id
#        #the '-1' dictates reverse looping order
#        for i in range( latest_email_id, numberOfmsg, -1 ):
#            status, data = self.client.fetch( i, '(RFC822)' )
#            print "===> Data: ", json.dumps(data)
#            for response_part in data:
#                if isinstance(response_part, tuple):
#                    msg = email.message_from_string(response_part[1])
#                    self.getbody(mail=msg)
#                    emailSubject = msg['subject']
#                    emailFrom = msg['from']
#                    emailTo = msg['to']
#        #remove the brackets around the sender email address
#        emailFrom = emailFrom.replace('<', '')
#        emailFrom = emailFrom.replace('>', '')
#
#        #add ellipsis (...) if subject length is greater than 35 characters
#        if len( emailSubject ) > 35:
#            emailSubject = emailSubject[0:32] + '...'
#
#        print '[From: ' + emailFrom.split()[-1] + '] ' + '[To: ' + emailTo + '] ' + emailSubject


    def getbody(self, mail=None):
        for part in mail.walk():
            # multipart are just containers, so we skip them
            if part.get_content_maintype() == 'multipart':
                continue 
            # we are interested only in the simple text messages
            if part.get_content_subtype() != 'plain':
                continue 
            payload = part.get_payload()
            print payload


#Extracting Attachmets
#    def getAttachments(self, mail=None):
#        for part in mail.walk():
#            # if multipart are containers, we skip it
#            if part.get_content_maintype() == 'multipart':
#                continue
#            # Check whether it is an attachment or not
#            if part.get('Content-Disposition') is None:
#                continue
#
#	        # get file name
#            filename = part.get_filename()
#            if not filename:
#                filename = name_pat.findall(part.get('Content-Type'))[0][6:-1]
#	        # get file type (only type): application, audio, image, message, text, video
#            filetype = part.get_content_type().split('/')[0]
#            # get file type (type/subtype)
#            contenttype = str(part.get_content_type())
#
#            # If a file does not have a name, creates one 
#            # TODO: I am not sure if I should create a name for a file
#            counter = 1
#            if not filename:
#                filename = 'part-%03d%s' % (counter, 'bin')
#                counter += 1
#
#            # get attachment's content
#            attachment = part.get_payload(decode=True)
#
#            # get file size
#            filesize = len(attachment)
#
#            data = None
#            if (filetype == 'application'):
#                datatype = 'APPLICATION'
#            elif (filetype == 'audio'):
#                datatype = 'AUDIO'
#            elif (filetype == 'image'):
#                datatype = 'IMAGE'
#            elif (filetype == 'message'):
#                datatype = 'MESSAGE'
#            elif (filetype == 'text'):
#                datatype = 'TEXT'
#                data = attachment
#            elif (filetype == 'video'):
#                datatype = 'VIDEO'
#            else:
#                datatype = 'OTHERS'
#
#            print "Done with getAttachments()"



    def storeEmail(self, emailId=None, data_type=None, data=None):
        try:
            service_data, created = GmailData.objects.get_or_create(email_id=str(emailId),neemi_user=self.user.neemi_user)
            service_data.gmail_user = self.user
            service_data.data_type = data_type

            try:
                json.dumps(data).decode('utf-8')
                service_data.data = data
            except UnicodeDecodeError: 
                text_data = json.dumps(data, ensure_ascii=False)
                text_data = convert2unicode(text_data)
                new_data = json.loads(text_data)
                service_data.data = new_data
                print "Email was converted to unicode!"
                pass

            for response_part in data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_string(response_part[1])
                    date = email.utils.parsedate(msg['Date'])
                    if date is not None:
                        date = datetime.datetime.fromtimestamp(time.mktime(date))
                    service_data.time = date
                    #date = msg['Date']
                    #service_data.time = date
                
            service_data.save() 
        except Exception as e:
            raise MyError(e)
        
            


