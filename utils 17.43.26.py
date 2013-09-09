#!/usr/bin/env python

import re, random, string
import hashlib
import hmac
import mydb
import datetime
from settings import COOKIE_SECRET


def hash_str(s):
    return hashlib.sha256(s).hexdigest()

secret = COOKIE_SECRET #"".join(random.sample(string.letters, 50))


def make_secure_val(s):
    return "%s|%s" % (s, hmac.new(secret, s).hexdigest())


def check_secure_val(h):
    val = h.split('|')[0]
    if h == make_secure_val(val):
        return val


def make_salt():
    return ''.join(random.sample(string.letters, 5))


def make_pw_hash(name, pw, hsh=None):
    if hsh:
        salt = hsh.split('|')[1]
    else:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)


def valid_pw(name, pw, h):
    new_h = make_pw_hash(name, pw, h)
    return new_h == h


def valid_name(name):
    USER_RE = re.compile(r"^[a-zA-Z\s]{3,20}$")
    return USER_RE.match(name)


def valid_psswrd(psswrd):
    PSSWRD_RE = re.compile(r"^.{3,20}$")
    return PSSWRD_RE.match(psswrd)


def valid_email(email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")
    return EMAIL_RE.match(email)


def verify_psswrd(orig, rep):
    return orig == rep


def user_exists(email):
    q = mydb.User.get_by_email(email)
    return not(q is None)

def convert_dob(dob):
	dob_str = str(dob).split('-')
	return datetime.date(int(dob_str[0]), int(dob_str[1]), int(dob_str[2]))
	
