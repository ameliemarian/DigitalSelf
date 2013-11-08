import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient

from models import *

def create_text_indexes(request,service=None):
    url = '/create_indexes/'
    db = get_db()
    print 'INDEX'
    print service

    if service=='facebook' or service == None:
        print 'ensure facebook index'
        db.facebook_data.ensure_index([("$**","text")],name="FacebookTextIndex")
    if service=='twitter' or service == None:
        print 'ensure twitter index'
        db.twitter_data.ensure_index([("$**","text")],name="TwitterTextIndex")
    if service=='foursquare' or service == None:
        print 'ensure foursquare index'
        db.foursquare_data.ensure_index([("$**","text")],name="FoursquareTextIndex")
    if service=='dropbox' or service == None:
        print 'ensure dropbox index'
        db.dropbox_data.ensure_index([("$**","text")],name="DropboxTextIndex")
    if service=='linkedin' or service == None:
        print 'ensure linkedin index'
        db.linked_in_data.ensure_index([("$**","text")],name="LinkedInTextIndex")
    if service=='googledrive' or service == None:
        print 'ensure googledrive index'
        db.gdrive_data.ensure_index([("$**","text")],name="GDriveTextIndex")
    if service=='gcal' or service == None:
        print 'ensure gcal index'        
        db.gcal_data.ensure_index([("$**","text")],name="GCalendarTextIndex")
    if service=='googlelattitde' or service == None:
        print 'ensure latitude index'
        db.g_latitude_data.ensure_index([("$**","text")],name="GoogleLatitudeTextIndex")

    return HttpResponseRedirect(url)

        
