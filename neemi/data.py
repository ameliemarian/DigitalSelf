import time,datetime
import os

from django.http import HttpResponseRedirect, HttpResponse

from .utils import cleanDict, cleanDictField
from .models import *
from .managers import *
from .plaid import PlaidHelper
from API.dropboxAPI import DropboxHelper
from API.twitterAPI import TwitterHelper
from API.linkedinAPI import LinkedInHelper
from API.foursquareAPI import FoursquareHelper
from API.facebookAPI import *
from API.twitterAPIData import *
from API.dropboxAPIData import *
from API.linkedinAPIData import *
from API.foursquareAPIData import *
from API.facebookAPIData import *
from API.googleAPIData import *

from mongoengine.queryset import DoesNotExist, MultipleObjectsReturned
from mongoengine.django.auth import User

#### THIS METHOD IS NOT BEING CALLED ANYWHERE
def get_all_user_data(request,service):
    print "get ALL Data From"
    print [service]
    #Singly uses deprecated handle gdocs for google drive

    url = '/get_data/'

    to_date = None
    from_date = None
    lastN = 500

    if request.user.is_authenticated():
        try:
            # handle each service separately
            if service == 'facebook':
                service_user = getFacebookProfile(request=request)
                getFacebookData(request=request,facebook_user=service_user,from_date=from_date,to_date=to_date,lastN=lastN)
#            elif service == 'gmail':
#                getSinglyServiceProfile(request=request,access_token=access_token,service=service)
#            elif service == 'gcal':
#                getSinglyServiceProfile(request=request,access_token=access_token,service=service)
#                getGoogleProxyServiceData(request=request,access_token=access_token, service=service,from_date=from_date,to_date=to_date,lastN=lastN)
            elif service == 'amex':
                getPlaidData(request=request,service=service)
#            elif service == 'dropbox':
#                current_dropbox_data = DropboxAPIData()
#                current_dropbox_data.getDropboxData(request=request,service=service)
#            elif service == 'twitter':
#                current_twitter_data = TwitterAPIData()
#                current_twitter_data.getTwitterData(request=request, service=service)
#            elif service == 'linkedin':
#                current_linkedin_data = LinkedInAPIData()
#                current_linkedin_data.getLinkedInData(request=request, service=service) 
#            elif service == 'foursquare':
#                current_foursquare_data = FoursquareAPIData()
#                current_foursquare_data.getFoursquareData(request=request, service=service) 
            elif (service == 'gmail' or service == 'gcal' or service == 'dropbox' or service == 'twitter' or service == 'linkedin' or service == 'foursquare'):
                print "Service does not support this option!"
            else:
                print "Unsupported service"
        except Exception as e:
            print "ERROR: ", e
    else:
        print "Unauthorized User"
    print [url]
    return HttpResponseRedirect(url)
        


def get_user_data(request,service,from_date=None,to_date=None,lastN=None):
    print "get Data From"
    print [service]
    url = '/get_data/'

    if request.user.is_authenticated():
        try:
            if service =='amex' and service not in request.user.plaid_services:
                views.authenticate_redirect(request,service)

            loop=False
            if from_date!=None:#  and to_date!=None:
                               # ONLY LOOP FROM A DATE, ensure we do not go far in the past
                loop=True
                if lastN is None:
                    lastN = 5000  

            # handle each service separately
            if service == 'facebook':
                service_user = getFacebookProfile(request=request)
                if from_date == "since_last":
                    if service_user.since != None:
                        from_date=int(time.mktime(service_user.since.timetuple()))//1*1000
                        lastN=5000
                        loop=True
                    else:
                        from_date=None ### NOT BEST CHOICE. IGNORES from last and get default

                getFacebookData(request=request,facebook_user=service_user,from_date=from_date,to_date=to_date,lastN=lastN)

                service_user.since = datetime.datetime.now()
                service_user.save()

            elif service == 'amex':
                getPlaidData(request=request,service=service)
            elif service == 'dropbox':
                current_dropbox_data = DropboxAPIData()
                current_dropbox_data.getDropboxData(request=request,service=service)
            elif service == 'twitter':
                current_twitter_data = TwitterAPIData()
                current_twitter_data.getTwitterData(request=request, service=service)
            elif service == 'linkedin':
                current_linkedin_data = LinkedInAPIData()
                current_linkedin_data.getLinkedInData(request=request, service=service) 
            elif service == 'foursquare':
                current_foursquare_data = FoursquareAPIData()
                current_foursquare_data.getFoursquareData(request=request, service=service)  
            elif service == 'gcal' or service == 'googleplus' or service == 'gmail' or service == 'googlecontacts':
                print "Processing service ", service
                current_gcal_data = GoogleAPIData()
                current_gcal_data.getGoogleData(request=request, service=service)             
            else:
                print "Unsupported service"
        except Exception as e:
            print "ERROR: ", e
            error_url = '/error/?message=%s' % e
            return HttpResponseRedirect(error_url)
    else:
        print "Unauthorized User"
        e = "Unauthorized User"
        error_url = '/error/?message=%s' % e
        return HttpResponseRedirect(error_url)

    print "URL: ", [url]
    return HttpResponseRedirect(url)


def getFacebookProfile(request):
        print 'Get profile from Facebook'
        currentuser = User.objects.get(username=request.user.username)
        facebook_user = FacebookUser.objects.get(neemi_user=currentuser.id)
        facebook = FacebookHelper()
        service_profile = facebook.make_request(access_token=facebook_user.access_token, request=request)        

        service_user, created = FacebookUser.objects.get_or_create(neemi_user=currentuser.id, access_token=facebook_user.access_token)
        #service_user.data = service_profile
	idr = 'profile:%s@facebook'%(service_user.userid)
	try:
		facebook_id = FacebookData.objects.get(idr=idr)
	except FacebookData.DoesNotExist:
		facebook_id = FacebookData(idr=idr, data=service_profile, neemiuser=currentuser.id, facebook_user=service_user, data_type='PROFILE', 
			time=datetime.datetime.today()).save()
        #service_user.since = datetime.datetime.today()
        service_user.save()
        print [service_user]
        print "done with Facebook"
        return service_user



def getPlaidData(request, service):
    print "Get Profile and Data from " + service
    ### HANDLES AMEX ONLY FOR NOW

    currentuser = User.objects.get(username=request.user.username)

    if service == 'amex':
        
        amex_profile, created = AmexUser.objects.get_or_create(neemi_user=currentuser)

        last_transaction = None

        #
        # FIX       
        #       if from_date == "since_last": #ONLY POSSIBLE OPTION, DEFAULT IS LAST 30 days
        #          print "SINCE"
        #   print [amex_profile.last_transaction_id]
        #   if amex_profile.last_transaction_id != None:
        #       last_transaction= amex_profile.last_transaction_id
        ##3  # loop=True I BELIEVE THERE IS NO LIMIT IN PLAID, NO NEED TO LOOP

        #CALL to PLAID gives both amex_profile and data

        plaid_request = {
            'access_token': amex_profile.plaid_access_token,
            'last':last_transaction
            }
        plaid_transactions, plaid_accounts = PlaidHelper.make_plaid_request(request=plaid_request)

        numberoffeeds = 0
        numbercreated = 0
        for value in plaid_transactions:
            numberoffeeds = numberoffeeds + 1
            trans_id = value['_id']

            amex_data, created = PlaidData.objects.get_or_create(transaction_id=trans_id,neemi_user=currentuser)
            if created == True:
                numbercreated = numbercreated + 1
                amex_profile.last_transaction_id = trans_id

                amex_data.amex_user = amex_profile
                amex_data.neemi_user = currentuser
                amex_data.transaction_id = trans_id
                amex_data.time = value['date']
                
                amex_data.data = value
                amex_data.save()

        for account in plaid_accounts:
            json_data = account['data']
            amex_profile.data = json_data
            amex_profile.last_updated = datetime.datetime.now()
            amex_profile.save()       
    else:
        print "unsupported service"


def getFacebookData(request, facebook_user, from_date, to_date, lastN, loop=False):
	currentuser = User.objects.get(username=request.user.username)
	singly_request = {
        	'access_token': facebook_user.access_token,
        	'since': from_date,
        	'until': to_date,
        	'limit': lastN
        }
	service_feeds = get_data(request=singly_request, currentuser=currentuser, service_user=facebook_user)


       

