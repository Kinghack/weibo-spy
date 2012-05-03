# coding=utf-8

import urllib,re,sys

import webapp2
from google.appengine.ext import webapp,db
from google.appengine.api import mail

sys.path.insert(0, 'weibopy.zip')
sys.path.append('weibopy.zip/weibopy')
sys.path.insert(0, 'tweepy.zip')
sys.path.append('tweepy.zip/tweepy')

import tweepy
from weibopy.auth import OAuthHandler
from weibopy.api import API
from weibopy.error import WeibopError 
from config import app_key , app_secret
from config import Mail_from , Mail_to


html_src = """
<html>
<head><title>Weibo-spy</title></head>
<body><center>
<h1>Weipo-Spy</h1>
<h3>Help to follow the tweet which you never want to miss</h3>
<form action="/result" method="post">
<table>
<tr><td>Sina email: </td><td><input type="text" name="s_name" /></td><td></td></tr>
<tr><td>监视对象屏显名称: </td><td><input type="text" name="god_name" /></td><td></td></tr>
<tr><td>Sina Oauth PIN: </td><td><input type="text" name="s_pin" /></td><td><a href="%s" target="_blank">Get Sina Oauth Pin</a></td></tr>
</table>
<input type="hidden" name="s_request_key" value="%s"><br>
<input type="hidden" name="s_request_secret" value="%s"><br>
<input type="submit" value="Submit">
</center></body>
</html>
"""


class OauthUser(db.Model):
    sina_name = db.StringProperty()
    sina_access_key = db.StringProperty()
    sina_access_secret = db.StringProperty()

class God(db.Model):
    user = db.ReferenceProperty(OauthUser,collection_name='god_name')
    god_name = db.StringProperty()
    sina_last_id = db.StringProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        sina = OAuthHandler(app_key,app_secret)
        sina_auth_url = sina.get_authorization_url()
        self.response.out.write(html_src % (sina_auth_url,sina.request_token.key,sina.request_token.secret))

class FormHandler(webapp2.RequestHandler):
    def post(self):
        s_name = self.request.get('s_name')
        s_request_key = self.request.get('s_request_key')
        s_request_secret = self.request.get('s_request_secret')
        s_pin = self.request.get('s_pin')
        self.response.out.write("""<html><head><title>Weibo-spy-result</title></head><body><center>""")
        if  s_name =="" or s_pin == "":
            self.response.out.write("""<h2>4 Input can not be empty! <a href="/">Back</a></h2>""")
        else:
            sina = OAuthHandler(app_key,app_secret)
            sina.set_request_token(s_request_key,s_request_secret)
            s_access_token = sina.get_access_token(s_pin.strip())
            sina_api = API(sina)

            

            #sina
            
            god_name = self.request.get('god_name')
            ttl = sina_api.user_timeline(screen_name=god_name)
            oauth_user = OauthUser(key_name=s_name)
            oauth_user.sina_name = s_name
            oauth_user.sina_access_key = s_access_token.key
            oauth_user.sina_access_secret = s_access_token.secret
            oauth_user.put()
    
            God(user=oauth_user,
                god_name=god_name,
                sina_last_id=str(ttl[0].id)).put()


            try:
                ttl = sina_api.user_timeline(screen_name=god_name)
            except WeibopError,e:
                self.response.out.write(e)
            else:
                self.response.out.write('Your spy settings are successfully done!<br>')
                self.response.out.write('The last tweet synchronized is below:<br>')
                for result in ttl:
                      self.response.out.write('<b>%s</b><br>' % result.text)
        self.response.out.write('</center></body></html>')


class AutoSync(webapp2.RequestHandler):
    def get(self):
        query = db.GqlQuery("SELECT * FROM OauthUser")
        if query.count() > 0:
            for result in query:
                sina = OAuthHandler(app_key,app_secret)
                sina.set_request_token(result.sina_access_key,result.sina_access_secret)
                sina_api = API(sina)
                
                for god in result.god_name:
                   ttl = sina_api.user_timeline(screen_name=god.god_name)
                   last_id = god.sina_last_id
                   tweet = "" 
                   for res in ttl:
                      if int(res.id) > int(last_id):
                         tweet = tweet + res.text + "  "
                   if len(tweet) > 0:
                       message = mail.EmailMessage()
                       message.subject = god.god_name
                       message.sender = Mail_from
                       message.to = Mail_to
                       message.body = """ 
%s
                       """ % tweet
                       message.send()
                       god.sina_last_id=str(ttl[0].id)
                       god.put()


app = webapp2.WSGIApplication(
    [('/', MainPage),
     ('/result', FormHandler),
     ('/cron', AutoSync),
     ],
    debug = True)


