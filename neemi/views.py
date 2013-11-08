from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from mongoengine.queryset import DoesNotExist
from mongoengine.django.auth import User

from plaid import PlaidHelper
from API.dropboxAPI import DropboxHelper
from API.twitterAPI import TwitterHelper
from API.foursquareAPI import FoursquareHelper
from API.linkedinAPI import LinkedInHelper
from API.googleAPI import GoogleHelper

#from models import NeemiUser
from .models import *
from managers import *
from data import *


def authenticate_redirect(request, service):
    print "auth_redirect"
    print [service]
  
    print request.user
    print request.COOKIES['sessionid']
    try:
        if request.user.is_authenticated():
            print "authenticated"
            if service == 'amex':
                current_plaid_helper = PlaidHelper()
                url = current_plaid_helper.get_authorize_url()
            elif service == 'dropbox':
                current_dropbox_helper = DropboxHelper()
                url = current_dropbox_helper.get_authorize_url(service)
                print url
            elif service == 'twitter':
                current_twitter_helper = TwitterHelper()
                url = current_twitter_helper.get_authorize_url(service)
            elif service == 'linkedin':
                current_linkedin_helper = LinkedInHelper()
                url = current_linkedin_helper.get_authorize_url(service)
            elif service == 'foursquare':
                current_foursquare_helper = FoursquareHelper()
                url = current_foursquare_helper.get_authorize_url(service)
            elif service == 'facebook':
                current_facebook_helper = FacebookHelper()
                url = current_facebook_helper.get_authorize_url()
            elif service == 'gcal' or service == 'googledrive' or service == 'googleplus' or service == 'gmail' or service == 'googlecontacts':
                request.session['google_service']=service
                current_google_helper = GoogleHelper()
                url = current_google_helper.get_authorize_url(request=request, service=service)
            else:
                print "SERVICE DOES NOT EXIST!"
                return HttpResponseRedirect('/register/') 

    #                return HttpRespocurrentuser.set_services({'facebook'})nseRedirect('/register/')
        else:
            print "USER NOT AUTHENTICATED"
            return HttpResponseRedirect('/register/')
    except Exception as e:
        print "ERROR: ", e

    print [url]
    return HttpResponseRedirect(url)


def neemi_login(request):
    print "neemi-login"
    username = request.POST['username']
    print username
    password = request.POST['password']
    try:
        currentuser = NeemiUser.objects.get(username=username)
        if currentuser.check_password(password):
            user = authenticate(username=username, password=password)
            auth_login(request,user)
            request.session.set_expiry(60 * 60 * 1) #1 hour timeout
            print [currentuser]
            print "Logged In"
            print request.user.username
            print request.COOKIES['sessionid']
            return HttpResponseRedirect('/')
        else:
            print "Login Failed - Wrong pw"
            return HttpResponseRedirect('/')
    except DoesNotExist:
        print "DOesNotExist _ Creating User"
        currentuser = NeemiUser.create_user(username=username, password=password)
        user = authenticate(username=username,password=password)
        auth_login(request, user)
        currentuser.save()
        return HttpResponseRedirect('/')

   
import time

def neemi_logout(request):
    print "Logout"
    # print [request]
    auth_logout(request)
    print request.user.username
    return HttpResponseRedirect('/')


def neemi_delete_user(request):
    print "Delete Neemi AND APIs user and logout"
    print [request.user.username]
    currentuser = User.objects.get(username=request.user.username)

    auth_logout(request)
    currentuser.delete()
    print "done"

    return HttpResponseRedirect('/')


def plaid_authorize_callback(request):
    print "plaid_authorize_callback"
    #print request.user.username
    code = request.GET.get('code')
    # print "code = "
    # print [code] 
    content = PlaidHelper.get_access_token(code)

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        amexuser, created = AmexUser.get_or_create(neemi_user=currentuser) 
        print [currentuser]
        print[amexuser]
        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            amexuser.access_token = content['access_token']
            currentuser.add_plaid_service('amex')#only one option for now

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"

    return HttpResponseRedirect('/register/')


def dropbox_authorize_callback(request):
    print "dropbox_authorize_callback"
    print request

    access_token = DropboxHelper.get_access_token()

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        dropboxuser, created = DropboxUser.objects.get_or_create(neemi_user=currentuser) 
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            dropboxuser.access_token_key = access_token.key
            dropboxuser.access_token_secret = access_token.secret
            dropboxuser.neemi_user = currentuser
            dropboxuser.save()

            currentuser.set_services({'dropbox'})
            #currentuser.set_dropbox_access_token(access_token.key,access_token.secret)

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"
    return HttpResponseRedirect('/register/')


def twitter_authorize_callback(request):
    print "twitter_authorize_callback"
    print request

    if 'oauth_verifier' in request.GET:
        oauth_verifier = request.GET.get('oauth_verifier')
    access_token, access_token_secret, userid, screenname = TwitterHelper.get_access_token(oauth_verifier)

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        twitteruser, created = TwitterUser.objects.get_or_create(neemi_user=currentuser)
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            currentuser.set_services({'twitter'})

            print "access_token: ", access_token
            print "access_token_secret: ", access_token_secret
            print "userid: ", userid
            print "screenname: ", screenname
            
            twitteruser.access_token_key = access_token
            twitteruser.access_token_secret = access_token_secret
            twitteruser.userid = userid
            twitteruser.screenname = screenname
            twitteruser.save()

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"
    return HttpResponseRedirect('/register/')


def linkedin_authorize_callback(request):
    print "linkedin_authorize_callback"
    print request

    if 'oauth_verifier' in request.GET:
        oauth_verifier = request.GET.get('oauth_verifier')
    access_token, access_token_secret, oauth_expires_in = LinkedInHelper.get_access_token(oauth_verifier)

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        linkedinuser, created = LinkedInUser.objects.get_or_create(neemi_user=currentuser)
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            currentuser.set_services({'linkedin'})

            print "access_token: ", access_token
            print "access_token_secret: ", access_token_secret
            
            # Store access token and expiration time
            linkedinuser.access_token_key = access_token
            linkedinuser.access_token_secret = access_token_secret
#            linkedinuser.access_token_expires_in = oauth_expires_in
#            linkedinuser.access_token_expires_at = int(time.time()) + oauth_expires_in
            linkedinuser.save()

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"
    return HttpResponseRedirect('/register/')


def foursquare_authorize_callback(request):
    print "foursquare_authorize_callback"
    print request

    if 'code' in request.GET:
        oauth_code = request.GET.get('code')
    else:
        print "Missing oauth code!"
        return

    access_token = FoursquareHelper.get_access_token(oauth_code)

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        foursquareuser, created = FoursquareUser.objects.get_or_create(neemi_user=currentuser)
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            currentuser.set_services({'foursquare'})

            print "access_token: ", access_token
            
            foursquareuser.access_token = access_token
            foursquareuser.save()

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"
    return HttpResponseRedirect('/register/')


def facebook_authorize_callback(request):
    print "facebook_authorize_callback"
#    print request

    if 'code' in request.GET:
        code = request.GET.get('code')
        print 'code: ' + code
    else:
        print "Missing oauth code!"
        return        

    facebookhelper = FacebookHelper()
    access_token = facebookhelper.get_access_token(code)
    userid, screenname = facebookhelper.get_user(access_token)
    
    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        facebookuser, created = FacebookUser.objects.get_or_create(neemi_user=currentuser)
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            currentuser.set_services({'facebook'})

            print "access_token: ", access_token
            
            facebookuser.access_token = access_token
            facebookuser.userid = userid
            facebookuser.screenname = screenname
            facebookuser.save()

    except DoesNotExist:
        print "DOesNotExist"
    print "Called back"
    return HttpResponseRedirect('/register/')


def google_authorize_callback(request):
    print "google_authorize_callback"
#    print request

    if 'code' in request.GET:
        code = request.GET.get('code')
        print 'code: ' + code
    else:
        print "Missing oauth code!"
        return        

    googlehelper = GoogleHelper()
    credentials = googlehelper.get_access_token(code)

    try:
        print [request.user.username]
        currentuser = User.objects.get(username=request.user.username)
        googleuser, created = GoogleUser.objects.get_or_create(neemi_user=currentuser)
        print [currentuser]

        if not currentuser.is_authenticated():
            print "ohoh Not Authenticated"
        else:
            print "updating user"
            currentuser.set_services({request.session['google_service']})
            del request.session['google_service']

            # If google user is being created, add profile data
            if (created):
                profile = googlehelper.get_userProfile()
                googleuser.user_id = profile['id']   
                googleuser.email_address = profile['email']

            googleuser.credentials = credentials
            googleuser.save()

    except DoesNotExist:
        print "DOesNotExist"    

    print "Called back"
    return HttpResponseRedirect('/register/')







