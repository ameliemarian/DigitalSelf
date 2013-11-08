// The URL of the Singly API endpoint
var apiBaseUrl = 'https://api.singly.com';

// A small wrapper for getting data from the Singly API
var singly = {
   get: function(url, options, callback) {
      if (options === undefined ||
         options === null) {
         options = {};
      }

      options.access_token = accessToken;
      $.getJSON(apiBaseUrl + url, options, callback);
   }
};

// Runs after the page has loaded
$(function() {
   // If there was no access token defined then return
   if (accessToken === 'undefined' ||
      accessToken === undefined) {
      return;
   }

   // Get the 5 latest items from the user's Twitter feed
   singly.get('/services/twitter/tweets', { limit: 5 }, function(tweets) {
      for (var i = 0; i < tweets.length; i++) {
         $('#twitter').append('<li><strong>Tweet:</strong> '+ tweets[i].data.text +'</li>');
      }
   });
});

