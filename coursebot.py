#!/usr/bin/python3
import praw
import pyrebase
import re
import requests
from bs4 import BeautifulSoup
from config import firebase, reddit
from time import sleep

# Subreddits to monitor, separated by '+'
SUBREDDITS = 'uoft+dcs_uoft+utsc+utm+skule'

# Regex constants
COURSE_NAME_REGEX = re.compile(r'[a-zA-Z]{3}\d{3}[h|H|y|Y]*[1]*')
COURSE_INFO_REGEX = re.compile(r'[a-zA-Z]{3}\d{3}[h|H|y|Y]{1}[1]{1}')

# Firebase initialization
fb = pyrebase.initialize_app(firebase)
db = fb.database()

# Reddit bot login, returns reddit object used to reply with this account
def login():
    r = praw.Reddit(username = reddit["username"],
                password = reddit["password"],
                client_id = reddit["client_id"],
                client_secret = reddit["client_secret"],
                user_agent = 'CourseBot v0.1')
    return r

# Update firebase 'serviced' with <item_id> to avoid multiple comments by bot
def updateServiced(item_id):
    payload = {item_id: True}
    db.child("serviced").update(payload)

# Check if <item_id> has already been replied to by bot
def isServiced(item_id):
    request = db.child("serviced").child(item_id).get().val()
    if request:
        return True
    return False

# Replaces course names in descriptions with links to course pages
def replaceNameWithLink(matchobj):
    course_name = matchobj.group(0)
    return '[' + course_name + ']' + '(http://calendar.artsci.utoronto.ca/crs_' + course_name[:3].lower() + '.htm#' + course_name + ')'

# Returns the course description to be used in the bot reply
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

# Check submissions and comments for course names and reply accordingly
def checkItem(item):
    skip = False
    try:
        course_mentioned = re.findall(COURSE_NAME_REGEX, item.title)
        lower_title = item.title.lower()
        if 'grade' in lower_title or 'mark' in lower_title:
            skip = True
    except AttributeError:
        course_mentioned = re.findall(COURSE_NAME_REGEX, item.body)
    if len(course_mentioned) == 1 and not isServiced(item.id) and not item.author.name == "CourseBot" and not skip:
        course_name = course_mentioned[0]
        reply = getCourseInfo(course_name.lower())
        if reply:
            reply = reply + '\n\n'
            pre = '###' + course_name.upper() + ':\n\n'
            post = '[Source Code](https://github.com/zuhayrx/coursebot)'
            reply = pre + reply + post
            try:
                item.reply(reply)
            except:
                sleep(5)
                return
            print(reply)
        updateServiced(item.id)
        sleep(5)

# Start scanning subreddits and comments for matches and act accordingly
def run(r):
    subreddits = r.subreddit(SUBREDDITS)
    subreddit_comments = subreddits.comments()
    subreddit_submissions = subreddits.new(limit=50)
    for comment in subreddit_comments:
        checkItem(comment)
    for submission in subreddit_submissions:
        checkItem(submission)

# Log in once
r = login()

# Every 5 minutes, scan subreddits and comments for matches and act accordingly
while True:
    run(r)
    sleep(300)