from django.db import models
from singly import *
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from models import FacebookUser

#this right now is daving singly information in user_profile and saving user session information (in User... soon)
# need to separate. should probably only be for sessions with a separate module for Singly. Need to think about code structure

