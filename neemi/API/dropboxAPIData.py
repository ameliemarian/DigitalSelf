import time, datetime
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
        print "Service_user: ", service_user

        print "access_token: ", service_user.access_token_key, service_user.access_token_secret
        dropbox_client = DropboxHelper.create_dropbox_client(service_user.access_token_key,
                                                             service_user.access_token_secret)
        print "Dropbox_client: ", dropbox_client

        path = '/'
        # path = '/CDF_VLDB/Code/wrong'
        getDropboxFiles(dropbox_client, path, currentuser)


def getDropboxFiles(dropbox_client, path, currentuser):
    # print "getting path: ", path

    service_data, created = DropboxData.objects.get_or_create(path=path, neemi_user=currentuser)
    # print "created: ", created

    # get metadata
    if created:
        metadata = dropbox_client.metadata(path)
        # print "metadata 1: ", metadata
    else:
        try:
            metadata = dropbox_client.metadata(path, hash=service_data.folderhash)
            # print "metadata 2: ", metadata
        except Exception, e:
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

    # print "Time: ", service_data.time

    if metadata['is_dir']:
        # update folder hash and metadata
        try:
            service_data.folderhash = metadata['hash']
            service_data.dropbox_user = DropboxUser.objects.get(neemi_user=currentuser)
            service_data.path = metadata['path']
            service_data.data_type = 'FOLDERS'
            service_data.data = metadata
            service_data.save()
        except Exception as e:
            print "Exception when trying to save dropbox folder->: ", e
            pass
        # print "ITS FOLDER"
        try:
            for item in metadata['contents']:
                getDropboxFiles(dropbox_client, item['path'], currentuser)
        except Exception as e:
            print "Exception when trying to get the dropbox files from folder-> ", e
            pass
    else:
        # print "path: ", metadata['path']
        try:
            fileData = dropbox_client.get_file(metadata['path'])
            service_data.path = metadata['path']
            service_data.data_type = 'FILES'
            service_data.data = metadata
            service_data.file_content = fileData.read()
            #revision_metadata = dropbox_client.revisions(metadata['path'])
            #service_data.revision_data = revision_metadata
            service_data.save()
            # print "ITS FILE"
        except Exception as e:
            print "Exception when trying to save a dropbox file: ", e
            pass
