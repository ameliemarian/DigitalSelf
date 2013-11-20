import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient

from models import *

def basic_stats():
    url = '/get_stats/'

    mongo_db = get_db()
    print [mongo_db]

    print "Database statistics: "
    dbStats = mongo_db.command("dbstats")
    print "Total size in bytes of the data held in this database: ", dbStats['dataSize']
    print "Average size of each document in bytes: ", dbStats['avgObjSize']
    print "Number of objects: ", dbStats['objects']
    print "Number of collections: ", dbStats['collections']
    print ""

    collectionsList = mongo_db.collection_names()
    print "Collections: "
    for item in collectionsList:
        if item.find('data') != -1:
            try:
                print "----"
                print item
                colStats = mongo_db.command("collstats", item)
                print "Number of documents: ", colStats['count']
                print "Collection size in bytes: ", colStats['size']
                print "Average object size in bytes: ", colStats['avgObjSize']
            except Exception as e:
                print 'Error:', e
                continue
    

    return HttpResponseRedirect(url)
