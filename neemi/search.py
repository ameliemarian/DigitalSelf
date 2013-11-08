import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient

from models import *

def simple_keyword_search(request,keyword,service=None):
    url = '/search/'
    if service == 'facebook':
        mongo_db = get_db()
        print [mongo_db]
        #facebook_items = FacebookData.objects(data__message.contains(keyword))
        #facebook_items = FacebookData.objects(data_type='FEED')
        facebook_items = mongo_db.command('text', 'facebook_data', search=keyword)
        #facebook_items = FacebookData.objects.command('text',
        for item in facebook_items['results']:
            # print item
            print '----'
            print item['obj']['time']
            if item['obj']['data'].has_key('message'):
                print item['obj']['data']['message']
        results = facebook_items
    else:
        results = None
    return HttpResponseRedirect(url)
        
