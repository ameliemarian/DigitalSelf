from django.db import models
from django.core.urlresolvers import reverse
from djangotoolbox.fields import ListField, EmbeddedModelField
from django.utils.encoding import smart_str
from django.contrib.auth.models import _user_get_all_permissions
from django.contrib.auth.models import _user_has_perm
from django.contrib.auth.models import AnonymousUser
from django.utils.translation import ugettext_lazy as _
from oauth2client.django_orm import CredentialsField

from mongoengine.django.auth import User as MongoUser
from mongoengine import *
#from managers import UserProfileManager


class NeemiUser(MongoUser):

    services = ListField(StringField(max_length=50),
                                verbose_name=_('List of Connected Services'))
    error_message_log = StringField(default = None,
                                    max_length=1000,
                            verbose_name=_('ERROR_LOG'))

    def set_services(self, api_services):
        for service in iter(api_services):
            print [service]
            if service not in self.services and service!='id' and service!='password':
                self.services.append(service)
        self.save()

    def has_google_service(self, google_service):
        if google_service not in self.services:
            return False
        return True

    def add_plaid_service(self, plaid_service):
        if plaid_service not in self.plaid_services:
            self.plaid_services.append(plaid_service)
        self.save()
 
class ServiceUser(DynamicDocument):

    # Trying to ust store the Singly BSON plus neemi info
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)

    idr = StringField(default = None,
                      max_length=260)

    last_updated = DateTimeField()
    earliest_data = DateTimeField()  # not needed for all services. e.g. calendars and drive always get all... I think... To check

    meta = {'allow_inheritance': True}


class AmexUser(ServiceUser): #one per user??
    service_name = StringField(default = "Amex")
    
    plaid_access_token = StringField()
    last_transaction_id = StringField()

 
class FoursquareUser(ServiceUser):
    service_name = StringField(default = "Foursquare")
    access_token = StringField()
    last_access = StringField(default = "0")


class TwitterUser(ServiceUser):
    service_name = StringField(default = "Twitter")
    access_token_key = StringField()
    access_token_secret = StringField()
    userid = StringField()
    screenname = StringField()
    since_id = IntField(default=0)
    #since_id = StringField(default = "0", max_length=260)


class GoogleUser(ServiceUser):
    service_name = StringField(default = "GoogleAPI")
    credentials = CredentialsField()
    user_id = StringField()
    email_address = StringField()

    # calendar
    last_calendar_access = DateTimeField()
    # email (gmail)
    last_email_access = DateTimeField()
    # contacts (address book)
    #last_contacts_access = DateTimeField()
    last_contacts_access = StringField()

    
class FacebookUser(ServiceUser):
    service_name = StringField(default = "Facebook")
    access_token = StringField()
    since = DateTimeField()


class LinkedInUser(ServiceUser):
    service_name = StringField(default = "LinkedIn")
    access_token_key = StringField()
    access_token_secret = StringField()
    access_token_expires_in = StringField(default = "0")
    access_token_expires_at = StringField(default = "0")
    modified_since = StringField(default = "0")
    groups = ListField(IntField())


class DropboxUser(ServiceUser):
    service_name = StringField(default = "Dropbox")
    access_token_key = StringField()
    access_token_secret = StringField()


############ Services Data ############


class AmexData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    amex_user = ReferenceField(AmexUser)    
    transaction_id = StringField(max_length=260)
    time = DateTimeField()
    meta = {'allow_inheritance': True}


class DropboxData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    dropbox_user = ReferenceField(DropboxUser)
    time = DateTimeField()
    folderhash = StringField(max_length=260)
    revision = StringField(max_length=260)
    path = StringField(max_length=260)
    file_content = StringField()
    TYPE = ('FILES','FOLDERS') 
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class FacebookData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    facebook_user = ReferenceField(FacebookUser)
    idr = StringField(max_length=260)
    feed_id = StringField(max_length=260)
    time = DateTimeField()
    TYPE = ('FEED','PHOTO','ALBUM','CHECKIN','EVENT','FRIEND','FAMILY','GROUP','INBOX','LINK','NOTE','POST','STATUS','HOME','PROFILE')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}
  

class FoursquareData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    foursquare_user = ReferenceField(FoursquareUser)    
    feed_id = StringField(max_length=260)
    time = DateTimeField()
    TYPE = ('BADGE','CHECKIN','FRIEND','PHOTO','RECENT')  
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class TwitterData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    twitter_user = ReferenceField(TwitterUser)
    time = DateTimeField()
    feed_id = StringField(max_length=260)
    TYPE = ('FAVORITE','MENTION','FRIEND','FOLLOWER','TWEET','TIMELINE', 'RETWEET', 'MSG_RECEIVED', 'MSG_SENT')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class LinkedInData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    linkedin_user = ReferenceField(LinkedInUser)
    time = DateTimeField()    
    idr = StringField(max_length=260)
    feed_id = StringField(max_length=260)
    TYPE = ('CONNECTION','UPDATE','NETWORK', 'PROFILE')   
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class GcalData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gcal_user = ReferenceField(GoogleUser)
    time = DateTimeField()
    calendar_id = StringField()    
    event_id = StringField(max_length=260)
    TYPE = ('METADATA', 'EVENT')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class GplusData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gplus_user = ReferenceField(GoogleUser)
    time = DateTimeField()
    feed_id = StringField(max_length=260)
    TYPE = ('PEOPLE', 'ACTIVITIES', 'COMMENTS')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


class GLatitudeData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gapi_user = ReferenceField(GoogleUser)
    # time = DateTimeField()
    location_id = StringField(max_length=260)
    meta = {'allow_inheritance': True}


class GdriveData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gapi_user = ReferenceField(GoogleUser)
    #time = DateTimeField()

    file_id = StringField()
    meta = {'allow_inheritance': True}


class GmailData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gmail_user = ReferenceField(GoogleUser)
    time = DateTimeField()
    email_id = StringField(max_length=260)
    TYPE = ('INBOX', 'SENT')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}

class GcontactsData(DynamicDocument):
    neemi_user = ReferenceField(NeemiUser,reverse_delete_rule=CASCADE)
    gcontacts_user = ReferenceField(GoogleUser)
    time = DateTimeField()
    feed_id = StringField(max_length=260)
    TYPE = ('CONTACT', 'GROUPS')
    data_type = StringField(max_length=12, choices = TYPE)
    meta = {'allow_inheritance': True}


