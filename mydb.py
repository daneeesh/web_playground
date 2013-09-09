#!/usr/env/bin python

import logging
import time
import datetime

from google.appengine.api import memcache
from google.appengine.ext import db


def recentposts(update=False):
    key = 'recent'
    age = 'age_recent'
    recent_posts = memcache.get(key)
    if recent_posts is None or update:
        logging.debug("CACHE QUERY RECENTPOSTS")
        recent_posts = allposts()[:10]
        memcache.set(key, recent_posts)
        memcache.set(age, time.time())
    return recent_posts


def allposts(update=False, newpost=None):
    key = 'all'
    #key2 = 'recent'
    age = 'age_recent'
    all_posts = memcache.get(key)
    if update and newpost:
        all_posts.append(newpost)
        memcache.set(key, all_posts)
    elif all_posts is None or update:
        logging.debug("DB QUERY ALLPOSTS")
        a = db.GqlQuery("SELECT * FROM Post ORDER BY created")
        all_posts = list(a)
        memcache.set(key, all_posts)
        #memcache.set(key2, all_posts[:10])
        memcache.set(age, time.time())
        print "finished updating all the posts"
    return all_posts


def singlepost(id):
    all_posts = allposts()
    entries = [post for post in all_posts if post.title == id]
    try:
        a = entries[-1]
        print "title: " + str(a.title)
        print "key: " + str(a.key())
    except:
        a = None
    return a


def allusers(update=False, newuser=None):
    key = 'users'
    all_users = memcache.get(key)
    if newuser and update and not(all_users is None):
        all_users.append(newuser)
        memcache.set(key, all_users)
        print "allusers in memcache replaced"
    elif all_users is None or update:
        logging.error("DB QUERY ALLUSERS")
        a = db.GqlQuery("SELECT * FROM User ORDER BY created")
        all_users = list(a)
        memcache.set(key, all_users)
    return all_users


def single_user_by_name(name):
    all_users = allusers()
    for user in all_users:
        if str(user.username) == str(name):
            return user
    return None


def initialize_memcache():
    allposts(True)
    allusers(True)


def flush_memcache():
    memcache.flush_all()


def memcache_get(key):
    return memcache.get(key)


def memcache_set(key, value):
    memcache.set(key, value)


class User(db.Model):
	email = db.StringProperty(required=True)
	first_name = db.StringProperty(required=True)
	last_name = db.StringProperty(required=True)
	password_hash = db.StringProperty(required=True)
	salt = db.StringProperty(required=True)
	dob = db.DateProperty(required=True)
	gender = db.StringProperty(required=True)
	occupation = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now=True)
	fb_id = db.StringProperty(required=False)
	fb_accesstoken = db.StringProperty(required=False)
	fb_profile = db.StringProperty(required=False)
	@classmethod
	def get_by_email(cls, email):
		return User.all().filter('email = ', email).get()


class Post(db.Model):
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    #last_modified = db.DateTimeProperty(auto_now=True)

    @classmethod
    def get_by_title(cls, title):
        return Post.all().filter('title = ', title).get()

class Posts(db.Model):
    title = db.StringProperty(required=True)
    content = db.StringListProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    last_modified = db.ListProperty(datetime.datetime)

    @classmethod
    def get_by_title_version(cls, title, version):
        ps = Posts.all().filter('title = ', title).get()
        if version <= len(ps.content):
            return Post(title=title, content=ps.content[version])
        else:
            return None

    @classmethod
    def get_latest_by_title(cls, title):
        ps = Posts.all().filter('title = ', title).get()
        if ps is None:
            return None
        else:
            return Post(title=title, content=ps.content[-1])

    @classmethod
    def get_all_versions(cls, title):
        return Posts.all().filter('title = ', title).get()

    @classmethod
    def add_new(cls, title, content):
        p = Posts.all().filter('title = ', title).get()
        print "p is not none is add_new"
        cont = p.content
        cont.append(content)
        print cont
        p.content = cont
        l = p.last_modified
        l.append(datetime.datetime.now())
        p.last_modified = l
        p.put()
        print p.content
        print p.last_modified