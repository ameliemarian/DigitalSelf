DigitalSelf
===========

The instructions below were tested on Linux only! Please, be aware that things are constantly changing and some installation commands may stop working. However, the package requirements are still the same.

Any comments or questions, please contact rutgersneemi@gmail.com

##### Installation 	
 - mongoDB 2.4.2  
   <http://www.mongodb.org>    
 - Python 2.7.5     
 - Django 1.5.1   
   <https://www.djangoproject.com>   
 - djangotoolbox (pip install djangotoolbox)
 - django-nonrel (pip install pip install git+https://github.com/django-nonrel/django@nonrel-1.5)  
 - pymongo 2.6.3 (pip install pymongo)
   <http://api.mongodb.org/python/current/index.html>      
 - mongoengine 0.8.2 (pip install mongoengine)
   <http://mongoengine.org>  
 - oauth2 (pip install oauth2)
   <http://oauth.net/2/>  
 - oauth2client (pip install oauth2client)
   <https://code.google.com/p/google-api-python-client/wiki/OAuth2Client>
 - requests (pip install requests) 
   <http://www.python-requests.org>     


##### APIs     
- Dropbox     
 Dropbox Module      
 <https://www.dropbox.com/developers/core/sdks/python>       
 pip install dropbox	        

- Facebook     
 Facebook requires changes to the rauth package:     
 1. download rauth  (pip install rauth)     
 2. find rauth installation on local machine — /usr/local/lib/python2.7/dist-packages/rauth — and replace files service.py and session.py by the ones provided in neemi/packages/rauth/     

- Foursquare       
 Python wrapper for the foursquare v2 API           
 <https://github.com/mLewisLogic/foursquare>         
 pip install foursquare       

- Linkedin     
	
- Twitter        
 Python wrapper for the Twitter API         
 <https://github.com/ryanmcgrath/twython>         
 pip install twython           

- Google         
 1. Google APIs Client Library for Python        
 <https://developers.google.com/api-client-library/python/start/installation>         
 pip install —upgrade google-api-python-client             
 2. Google Data API                
 pip install gdata                     


##### Configuration 
- Django settings
  Edit file DigitalSelf/webapps/settings.py specifying name of database to be created to store all user data:
		Example - connect(‘digital_self’)

- keys.py
  To be able to access an API the user has to register an application with their services. During registrations, the API’s will provide at least a pair of id/secrets for each application registered and each application can serve multiple users.
  A skeleton of the keys.py file can be found in DigitalSelf/webapp/keys.py
  
  1. Registering a Dropbox application:
	Go to <https://www.dropbox.com/developers/apps> and follow the steps to create a new application. At the end, add the app key and secret to the keys.py file.
    Use the following arguments while creating the Dropbox application:
    - Status: Development
    - Permission type: Full Dropbox
    - OAuth redirect URIs: (you can leave it empty)
    - Drop-ins domains: (you can leave it empty)     

  2. Registering a Twitter application:
    Go to <https://dev.twitter.com/apps> and follow the steps to create a new application. At the end, add the consumer key and secret to the file keys.py.
	Use the following arguments while creating the Twitter application:
	- Access level: Read, write, and direct messages
	- Callback URL: (not relevant)

  3. Registering a LinkedIn application
	Go to <http://developer.linkedin.com/documents/authentication>. Step 1 explain how to create a new application. Once you've registered your LinkedIn app, you will be provided with an API key and secret key that should be added to the keys.py file.
	Use the following arguments while creating the Linkedin application:
    - In OAuth User Agreement, check options: r_network, rw_groups, r_fullprofile, r_contactinfo, rw_nus. There is no need to set any of the Redirect URLs.

  4. Registering a Foursquare application
    Go to <https://foursquare.com/developers/apps> and follow the steps to create a new application. At the end, add the client id and secret to the file keys.py.
	Use the following arguments while creating the Foursquare application:
    - Web Addresses:
      - Download / welcome page url: (not relevant)
      - Your privacy policy url: (not relevant)
      - Redirect URI(s): <http://lvh.me:8000/foursquare_authorize/callback>

  5. Registering a Facebook application
	Go to <https://developers.facebook.com/apps> and follow the steps to create a new application. Client id and secret should be added to the file keys.py.

  6. Registering a Google application (The instructions below are following the old console interface, that can still be used. A new console is available and the instructions will be a little bit different. For the new console you will find the credentials and services under the option APIs & auth.)
   Go to <https://code.google.com/apis/console> and register a new application. In the option “API Access” you can find your client id and secret. Besides that, you will have to enable each service that you are planning to use. It can be done under “Services”.
	Use the following arguments while creating the Google application:
    - Redirect URIs: <http://lvh.me:8000/google_authorize/callback>


##### Usage
- Start mongoDB
  <http://docs.mongodb.org/manual/tutorial/manage-mongodb-processes/>

- Start server and call app interface
  - Open a terminal, go to your local copy of the DigitalSelf code and type:
    python manage.py runserver

    More details can be found in: 
			<https://docs.djangoproject.com/en/1.5/intro/tutorial01/>

  - Open a browser and type:
    lvh.me:8000

- The DigitalSelf interface
  - The first page asks for a user and password. A new user does not need to be registered a priori to have access to the application. The registration is done as soon as the user enters with the desired username and password. 
  - In the main page the user can choose between the following options:
	- Register for Services: show all APIs implemented allowing users to register with a variety of different services.
	- Get Data from Services: user can get as much data as allowed by the APIs. This step requires the user to be authenticated with the service (Register for Services) before any data can be requested.
	- Search your Data (Not working on this version)
	- Delete Account and Data: clean all user data from database

- The data collected
  One data collection is created for each service implemented: dropbox_data, facebook_data, foursquare_data, gcal_data, gcontacts_data, gmail_data, gplus_data, linked_in_data and twitter_data.
  In mongoDB, collections are composed by documents. Each document represents an unique data retrieved from a service. Most documents have the following fields:
	- data: contains the raw data retrieved
	- data_type: specifies the type of data collected (e.g. Facebook feed, Facebook photo)
	- {service}_user: user authenticated to access the specific service (API)
	- neemi_user: DigitalSelf user
	- time: time the data was retrieved or time the data was originally created

	Some observations:		
	- Dropbox:
	Metadata and content are retrieved. Metadata is stored in the field “data” and a file content is stored in the field “file_content”. 
	- Gmail
	Metadata and content are retrieved, both are stored in the field “data”


##### Possible problems

- Foursquare - SSL3 certificate verify failed
  <http://stackoverflow.com/questions/13321302/python-foursquare-ssl3-certificate-verify-failed>

  1. Download <http://curl.haxx.se/ca/cacert.pem>
     wget <http://curl.haxx.se/ca/cacert.pem>

  2. Go to Python httplib2 dir (/usr/local/lib/python2.7/dist-packages/httplib2)
     cd /usr/local/lib/python2.7/dist-packages/httplib2

  3. Backup the current certificate
     cp cacerts.txt backup_cacerts.txt

  4. Copy the downloaded file and rename it as cacerts.txt
	 mv cacert.pem cacerts.txt 

