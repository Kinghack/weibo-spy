# coding=utf-8

import sys

import webapp2
from google.appengine.ext import db
from google.appengine.api import mail

from weibo import APIClient
from config import APP_KEY , APP_SECRET, CALLBACK_URL
from config import Mail_from , Mail_to


spy = """
<html>
<head><title>Weibo-spy-dev</title></head>
<body><center>
<h1>Weipo-Spy</h1>
<h3>Help to follow the tweet which you never want to miss</h3>
<form action="/result" method="post">
<table>
<tr><td>监视对象屏显名称: </td><td><input type="text" name="god_name" /></td><td></td></tr>
</table>
<input type="hidden" name="access_token" value="%s"><br>
<input type="hidden" name="expires_in" value="%s"><br>
<input type="submit" value="Submit">
</center></body>
</html>
"""

index = """
<html>
<head><title>Weibo-spy-dev</title></head>
<body><center>
<h1>Weipo-Spy</h1>
<h3>Help to follow the tweet which you never want to miss</h3>
<form action="/result" method="post">
<table>
<tr><td><a href="%s" target="_blank">登录微博</a></td></tr>
</table>
</center></body>
</html>
"""



class OauthUser(db.Model):
    sina_uid = db.StringProperty()
    sina_access_token = db.StringProperty()
    sina_expires = db.IntegerProperty()

class God(db.Model):
    user = db.ReferenceProperty(OauthUser,collection_name='god_name')
    god_name = db.StringProperty()
    sina_last_id = db.StringProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
	code = self.request.get('code') or None
	client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, 
		        redirect_uri=CALLBACK_URL)
	if not code:
		url = client.get_authorize_url()
        	self.response.out.write(index % (url))
	else:
		r = client.request_access_token(code)
		access_token = r.access_token
		expires_in = r.expires_in
		client.set_access_token(access_token, expires_in)
		info = client.statuses.user_timeline.get()
	    	oauth_user = OauthUser(key_name=info['statuses'][0]['user']['idstr'])
	    	oauth_user.sina_uid = info['statuses'][0]['user']['idstr']
	    	oauth_user.sina_access_token = str(access_token)
	    	oauth_user.sina_expires = expires_in
	    	oauth_user.put()
        	self.response.out.write(spy % (oauth_user.sina_access_token, oauth_user.sina_expires))

class FormHandler(webapp2.RequestHandler):
    def post(self):
	god_name = self.request.get('god_name')
	access_token = self.request.get('access_token')
	expires_in = self.request.get('expires_in')
        self.response.out.write("""<html><head><title>Weibo-spy-result</title></head><body><center>""")
        if  god_name == "":
            self.response.out.write("""<h2>4 Input can not be empty! <a href="/">Back</a></h2>""")
        else:

            client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, 
			     redirect_uri=CALLBACK_URL)
	    client.set_access_token(access_token, expires_in)
            info = client.statuses.user_timeline.get()
	    #可以考虑cookie
	    oauth_user = OauthUser(key_name=info['statuses'][0]['user']['idstr'])
	    oauth_user.sina_uid = info['statuses'][0]['user']['idstr']
	    oauth_user.sina_access_token = str(access_token)
	    oauth_user.sina_expires = int(expires_in)

	    status = client.statuses.user_timeline.get(screen_name=god_name)

                
            God(user=oauth_user,
                god_name=god_name,
                sina_last_id=str(status['statuses'][0]['id'])).put()

            self.response.out.write('Your spy settings are successfully done!<br>')
            self.response.out.write('The last tweet synchronized is below:<br>')
            for result in status['statuses']:
            	self.response.out.write('<b>%s</b><br>' % result.text)
        self.response.out.write('</center></body></html>')


class AutoSync(webapp2.RequestHandler):
    def get(self):
        query = db.GqlQuery("SELECT * FROM OauthUser")
        if query.count() > 0:
            for result in query:
            	client = APIClient(app_key=APP_KEY, app_secret=APP_SECRET, 
				     redirect_uri=CALLBACK_URL)
	    	client.set_access_token(result.sina_access_token, result.sina_expires)
                
                for god in result.god_name:
                   ttl = client.statuses.user_timeline.get(screen_name=god.god_name, since_id=god.sina_last_id)
                   tweet = "" 
		   if len(ttl['statuses']) > 0:
                   	god.sina_last_id=ttl['statuses'][0]['idstr']
                   	god.put()
                   for res in ttl['statuses']:
                    	   tweet = tweet + res.text + "NEXT"
                   if len(tweet) > 0:
                           message = mail.EmailMessage()
                           message.subject = god.god_name
                           message.sender = Mail_from
                           message.to = Mail_to
                           message.body = """ 
%s
                           """ % tweet
                           message.send()


app = webapp2.WSGIApplication(
    [('/', MainPage),
     ('/result', FormHandler),
     ('/cron', AutoSync),
     ],
    debug = True)

