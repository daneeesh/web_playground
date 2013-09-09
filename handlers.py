#!/usr/bin/env python

import os
import webapp2
import jinja2
import json
import time
import utils
import mydb
import cgi
import logging
import datetime
from settings import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, FACEBOOK_SECRET
import facebook

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape=False)
fblogin = "https://graph.facebook.com/oauth/authorize?client_id="+FACEBOOK_APP_ID+"&redirect_uri=http://sesh-test.appspot.com/use_facebook&state="+FACEBOOK_SECRET+"&scope=user_about_me,user_birthday,user_location"

class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)


    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)


    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


    def signedin(self):
        try:
            user_id_cookie_val = self.request.cookies.get('user_id')
            user_id_val = utils.check_secure_val(user_id_cookie_val)
            print "user_id_val: %s" % user_id_val
            if user_id_val:
                user = mydb.User.get_by_id(int(user_id_val))
                print "user: " + str(user)
                if not (user is None):
                    return user, True
            else:
                return None, False
        except:
            return None, False

    def logged_in(self):
        user = facebook.get_user_from_cookie(self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
        if user:
            graph = facebook.GraphAPI(user["access_token"])
            return True, graph
        else:
            return False, None


class SignupHandler(Handler):

    def render_signup(self, first_name="", login_err="", input_err="", email="", last_name="", gender="", occupation=""):
		loggedin, graph = self.logged_in()
		if loggedin:
			profile = graph.get_object("me")
			user_name = profile["name"]
			profile_pic = graph.fql("SELECT url FROM profile_pic WHERE id=%s AND width=%i AND height=%i" % (profile["id"], 40, 40))
			prof_pic = profile_pic["data"][0]["url"]
		else:
			user_name=None
			prof_pic=None
		self.render("get_started.html",
					first_name=first_name,
					login_err=login_err,
					input_err=input_err,
					email=email,
					last_name=last_name,
					gender=gender,
					occupation=occupation,
					FB_APP_ID=FACEBOOK_APP_ID,
					logged_in=loggedin,
					user_name=user_name,
					profile_pic=prof_pic)


    def get(self):
        self.render_signup()


    def post(self):
		if self.request.get('login_email') and self.request.get('login_password'):
			user_email = self.request.get('login_email')
			user_psswrd = self.request.get('login_password')

			print user_email

			valid_pwd = False
			valid_email = False

			q = mydb.User.get_by_email(user_email)
			if not(q is None):
				valid_email = True
				valid_pwd = utils.valid_pw(user_email, user_psswrd, q.password_hash)

				if valid_pwd and valid_email:
					self.response.headers.add_header('Set-Cookie', "user_id=%s;Path=/" % utils.make_secure_val(str(q.key().id())))
					self.redirect('/hello')
				else:
					self.render_signup(email=cgi.escape(user_email), login_err="Invalid username or password. Please sign up or try again.")
		else:
			user_email = self.request.get('email')
			user_psswrd = self.request.get('password')
			user_first_name = self.request.get('first_name')
			user_last_name = self.request.get('last_name')
			user_dob = self.request.get('dob')
			user_gender = self.request.get('gender')
			user_occupation = self.request.get('occupation')
			user_confirmation = self.request.get('confirmation')

			print user_email
			print user_psswrd
			print user_first_name
			print user_last_name
			print utils.convert_dob(user_dob)
			print user_gender
			print user_occupation
			print user_confirmation

			name = utils.valid_name(user_first_name) and utils.valid_name(user_last_name)
			user_ex = utils.user_exists(user_email)
			psswrd = utils.valid_psswrd(user_psswrd)
			email = utils.valid_email(user_email)

			# this will store the values to be returned
			#ret = {"uname":cgi.escape(user_uname), "uname_err":"", "psswrd_err":"", "verify_err":"", "email":cgi.escape(user_email), "email_err":""}

			if not name or user_ex or not psswrd or not email:
				input_err = "Some input was incorrect. Further details to come soon."
			if not(name and not user_ex and psswrd and email):
				self.render_signup(first_name=first_name,
				login_err=login_err,
				input_err=input_err,
				email=email,
				last_name=last_name,
				gender=gender,
				occupation=occupation)
			else:
				password_hash = utils.make_pw_hash(user_email, user_psswrd)
				user = mydb.User(first_name=user_first_name, last_name=user_last_name, dob=utils.convert_dob(user_dob), gender=user_gender, occupation=user_occupation, password_hash=password_hash, salt=password_hash.split('|')[1], email=user_email)
				user.put()
				print "added new user %s" % user.email
				#mydb.allusers(True, user)
				time.sleep(0.2)
				self.response.headers.add_header('Set-Cookie', "user_id=%s;Path=/" % utils.make_secure_val(str(user.key().id())))
				self.redirect('/hello')


class LogoutPage(Handler):

    def get(self):
        self.response.set_cookie('user_id', '')
        self.redirect('/get_started')


class HelloHandler(Handler):
	
	def get(self):
		user_hash = self.request.cookies.get('user_id')
		user, logged_in = self.signedin()
		if logged_in:
			self.response.out.write("Hello %s %s!<br>Your email is: %s<br>Your date of birth is %s<br>You're a %s and a(n) %s." % (user.first_name, user.last_name, user.email, user.dob.strftime("%c"), user.gender, user.occupation))
		else:
			self.redirect('/get_started')

class FacebookHandler(Handler):
					
	def get(self):
		user = facebook.get_user_from_cookie(self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
		if user:
			graph = facebook.GraphAPI(user["access_token"])
			profile = graph.get_object("me")
			friends = graph.get_connections("me", "friends")
			profile_pic = graph.fql("SELECT url FROM profile_pic WHERE id=%s AND width=%i AND height=%i" % (profile["id"], 40, 40))
			print profile_pic
			self.response.out.write("YAY<br>Welcome, %s!<br><img src=\"%s\"></img>" % (profile["name"], profile_pic["data"][0]["url"]))
		else:
			self.response.out.write("nay :(")