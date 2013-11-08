import time,datetime
import os

from neemi.models import *
from dropboxAPI import DropboxHelper

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

class DropboxAPIData(object):

    def getDropboxProfile(self, request):
        print "Get Profile Data from dropbox"
            
        currentuser = User.objects.get(username=request.user.username)
        service_user, created = DropboxUser.objects.get_or_create(neemi_user=currentuser)       

        service_user.neemi_user = currentuser

        key, secret = currentuser.get_dropbox_access_token()

        service_user.access_token_key = key
        service_user.access_token_secret = secret
    
        service_user.save()
        print [service_user]
        print "done dropbox profile"
        return service_user



    def getDropboxData(self, request, service):
        print "Get Data from " + service

        currentuser = User.objects.get(username=request.user.username)
        service_user = DropboxUser.objects.get(neemi_user=currentuser)

        print "access_token: ", service_user.access_token_key, service_user.access_token_secret
        dropbox_client = DropboxHelper.create_dropbox_client(service_user.access_token_key, service_user.access_token_secret)

        path = '/'
        #path = '/CDF_VLDB/Code/wrong'
        getDropboxFiles(dropbox_client, path, currentuser)



def getDropboxFiles(dropbox_client, path, currentuser):
 
    service_data, created = DropboxData.objects.get_or_create(path=path,neemi_user=currentuser)  

    # get metadata
    if created:
        metadata = dropbox_client.metadata(path)
    else:
        try:
            metadata = dropbox_client.metadata(path, hash=service_data.folderhash)
        except Exception,e: 
            print str(e), " - ", path
            return

    # update date/time file/folder was last modified
    if path == '/':
        service_data.time = datetime.datetime.now()
    else:
        service_data.time = metadata['modified'] 
        # update folder revision number
        # The root path does not have revision number
        service_data.revision = metadata['rev']
    print "Time: ", service_data.time

    # update folder hash and metadata
    service_data.folderhash = metadata['hash']
    service_data.data = metadata

    # new folder: add path, hash, revision number, metadata
    if created: 
        service_data.dropbox_user = DropboxUser.objects.get(neemi_user=currentuser)
        service_data.path = metadata['path']
        service_data.data_type = 'FOLDERS'
           
    service_data.save()
 

    for item in metadata['contents']:
        if item['is_dir']:
            getDropboxFiles(dropbox_client, item['path'], currentuser)
        else:
            # pymongo: strings in documents must be valid utf 8. To avoid problems 
            # We are only getting content from text/plain files
            if item['mime_type'] != 'text/plain':
                continue

            service_data, created = DropboxData.objects.get_or_create(path=item['path'],neemi_user=currentuser)    

            service_data.time = item['modified']

            if created:
                service_data.dropbox_user = DropboxUser.objects.get(neemi_user=currentuser)
                service_data.path = item['path']
                service_data.data_type = 'FILES'
                f, f_metadata = dropbox_client.get_file_and_metadata(item['path'])
                service_data.data = f_metadata
                service_data.file_content = f.read()
                service_data.revision = f_metadata['rev']
            else:
                f, f_metadata = dropbox_client.get_file_and_metadata(item['path'])
                if metadata['rev'] != f_metadata['rev']:
                    service_data.file_content = f.read()
                    service_data.revision = f_metadata['rev']
                    service_data.data = f_metadata

            service_data.save()
