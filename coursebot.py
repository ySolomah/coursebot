#!/usr/bin/python3
import praw
import pyrebase
import re
import requests
from bs4 import BeautifulSoup
from config import firebase, reddit
from time import sleep

SUBREDDITS = 'uoft+dcs_uoft+utsc+utm'
COURSE_NAME_REGEX = re.compile(r'[a-zA-Z]{3}\d{3}[h|H|y|Y]*[1]*')
COURSE_INFO_REGEX = re.compile(r'[a-zA-Z]{3}\d{3}[h|H|y|Y]{1}[1]{1}')

fb = pyrebase.initialize_app(firebase)
db = fb.database()

def login():
    r = praw.Reddit(username = reddit["username"],
                password = reddit["password"],
                client_id = reddit["client_id"],
                client_secret = reddit["client_secret"],
                user_agent = 'CourseBot v0.1')
    return r

def commentIsServiced(comment_id):
    payload = {comment_id: True}
    db.child("serviced").update(payload)

def isCommentServiced(comment_id):
    request = db.child("serviced").child(comment_id).get().val()
    if request:
        return True
    return False

def replaceNameWithLink(matchobj):
    course_name = matchobj.group(0)
    return '[' + course_name + ']' + '(http://calendar.artsci.utoronto.ca/crs_' + course_name[:3].lower() + '.htm#' + course_name + ')'

def getCourseInfo(course_name):
    url = 'http://calendar.artsci.utoronto.ca/crs_' + course_name[:3] + '.htm'
    try:
    	request = requests.get(url)
    except:
    	return ''
    html_content = request.text
    soup = BeautifulSoup(html_content, 'lxml')
    for item in soup.find_all('a'):
        try:
            if item['name'][:6] == course_name.upper():
                info = item.find_next_sibling('p').text
                info = re.sub(COURSE_INFO_REGEX, replaceNameWithLink, info)
                return info
        except KeyError:
            pass
    return ''

def run(r):
    subreddits = r.subreddit(SUBREDDITS)
    subreddit_comments = subreddits.comments()
    for comment in subreddit_comments:
        course_mentioned = COURSE_NAME_REGEX.search(comment.body)
        if course_mentioned and not isCommentServiced(comment.id) and not comment.author.name == "CourseBot":
            sleep(5)
            course_name = course_mentioned.group(0)
            reply = getCourseInfo(course_name.lower())
            if reply:
                reply = reply + '\n\n'
                pre = '###' + course_name.upper() + ':\n\n'
                post = '[Source Code](https://github.com/zuhayrx/coursebot)'
                reply = pre + reply + post
                comment.reply(reply)
            commentIsServiced(comment.id)

r = login()
while True:
	run(r)
	sleep(300)