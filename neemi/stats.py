import time,datetime

from django.http import HttpResponseRedirect, HttpResponse

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User
from mongoengine.connection import get_db

from pymongo import MongoClient

from models import *

class DBAnalysis(object):

    def __init__(self, request=None):
        self.url = '/get_stats/'
        self.mongo_db = get_db()
        self.file = open('statistic.txt', 'a')
        self.html_stats = []

        print "mongoDB: ", self.mongo_db
        print "username: ", request.user.username

        cursor = self.mongo_db['user'].find({'username':request.user.username})

        self.currentuser = ''
        for data in cursor:
            if '_id' in data.keys():                
                self.currentuser = data['_id']


    def basic_stats(self):
        print [self.mongo_db]
        self.printStats(text = "\n ------------------------------------ \n")
        self.printStats(text = "===> Statistics - " + time.strftime("%c"))

        dbStats = self.mongo_db.command("dbstats")

        self.printStats(text = "Total size in bytes of the data held in this database: " + str(dbStats['dataSize']))
        self.file.write("Average size of each document in bytes: " + str(dbStats['avgObjSize']) + '\n')
        self.printStats(text = "Number of objects: " + str(dbStats['objects']))
        self.printStats(text = "Number of collections: " + str(dbStats['collections']))
        self.printStats(text = "")

        collectionsList = self.mongo_db.collection_names()
        self.printStats(text = "Collections: ")
        for item in collectionsList:
            if item.find('data') != -1:
                try:
                    self.printStats(text = "----")
                    self.printStats(text = item)

                    colStats = self.mongo_db.command("collstats", item)
                    self.printStats(text = "Number of documents: " + str(colStats['count']))
                    self.printStats(text = "Collection size in bytes: " + str(colStats['size']))
                    if (colStats['count'] > 0):
                        self.printStats(text = "Average object size in bytes: " + str(colStats['avgObjSize']))
                    self.printStats(text = "")
                    self.collectionAnalysis(collection = item)
                except Exception as e:
                    print 'Error:', e
                    continue

        #return HttpResponseRedirect(self.url)
        return self.html_stats


    def collectionAnalysis(self, collection=None):
        dbcollection = self.mongo_db[collection]
        docs = dbcollection.find({"neemi_user" : self.currentuser})

        data_types = set()
        count = {}

        if (collection == 'dropbox_data') or (collection == 'facebook_data') or (collection == 'gcal_data') or (collection == 'linked_in_data') or (collection == 'gmail_data') or (collection == 'foursquare_data'):
            for data in docs:
                if 'data_type' in data.keys():                
                    data_type = data['data_type']
                    count[data_type] = count.get(data_type, 0) + 1   
#                else:
#                    print data
        elif (collection == 'gcontacts_data'):
            for data in docs:
                if 'data_type' in data.keys():
                    data_type = data['data_type']
                    count[data_type] = count.get(data_type, 0) + 1
                    string = data['data'][1:len(data['data']) - 1] 
        elif (collection == 'gplus_data'):   
            for data in docs:
                if 'data_type' in data.keys():
                    data_type = data['data_type']
                    count[data_type] = count.get(data_type, 0) + 1
#                else:
#                    print data
        elif (collection == 'twitter_data'):
            friends = set()
            followers =set()
            for data in docs:
                if 'data_type' in data.keys():
                    #print data['data'][0][1]
                    #return
                    data_type = data['data_type']
                    if data_type == 'FRIEND':
                        friends.add(data['data']['screen_name'])
                    elif data_type == 'FOLLOWER':
                        followers.add(data['data']['screen_name'])
                    elif data_type == 'TIMELINE':
                        #print data['data'].keys()
                        pass
                    count[data_type] = count.get(data_type, 0) + 1
#                else:
#                    print data

        for x in count: 
            self.printStats(text = str(x) + ': ' + str(count[x]))

    def printStats(self, text=None):
        print text
        self.file.write(text + '\n')
        self.html_stats.append(text)
        
                                    

     



