#!/usr/bin/env python
import praw
import pyrebase
import re
import requests
from bs4 import BeautifulSoup
from config import firebase, reddit
from time import sleep
import json


# Subreddits to monitor, separated by '+'
SUBREDDITS = 'testingground4bots'
courseBotName = reddit["username"]
dbIncrement = "5"
NewTestDb = "itemIdDb" + dbIncrement
CourseDb = "courseDb" + dbIncrement

# Regex constants
COURSE_NAME_REGEX = re.compile(r'[!]*[a-zA-Z]{3}[0-9]{3}[h|H|y|Y]*[1]*')
COURSE_INFO_REGEX = re.compile(r'[a-zA-Z]{3}[0-9]{3}[h|H|y|Y]{1}[1]{1}')

# Firebase initialization

fb = pyrebase.initialize_app(firebase)
db = fb.database()

# Reddit bot login, returns reddit object used to reply with this account
def login():
    r = praw.Reddit(username = reddit["username"],
                password = reddit["password"],
                client_id = reddit["client_id"],
                client_secret = reddit["client_secret"],
                user_agent = 'BetterCourseBot')
    print("Logged in");
    return r

# Update firebase 'serviced' with <item_id> to avoid multiple comments by bot
def updateServiced(item_id):
    print("Updating service");
    payload = {item_id: True}
    db.child(NewTestDb).update(payload)

#def setFalse(item_id):
#    payload = { item_id: False }
#    db.child(NewTestDb).update(payload);

# Check if <item_id> has already been replied to by bot
def isServiced(item_id):
    request = db.child(NewTestDb).child(item_id).get().val()
    if request:
        print("Already serviced: " + item_id)
        return True
    print("Not serviced yet: " + item_id)
    return False

# Replaces course names in descriptions with links to course pages
def replaceNameWithLink(matchobj):
    course_name = matchobj.group(0)
    return '[' + course_name + ']' + '(http://calendar.artsci.utoronto.ca/crs_' + course_name[:3].lower() + '.htm#' + course_name + ')'

# Returns the course description to be used in the bot reply
def getCourseInfo(course_name):
    print("Course name matched: " + course_name);
    url = 'https://timetable.iit.artsci.utoronto.ca/api/20169/courses?org=' + course_name[:3]
    try:
        request = requests.get(url)
    except:
        return ''
    html_content = request.text
    #print(html_content);

    data = json.loads(html_content);

    #print("Json length: " + str(len(data)));

    #for count in range(0, len(data)):
    #    print("Count is: " + str(count));
    #    print("Data: " + data[count]);

    if(len(data) > 0):
        for datainfo in data:
            #print("Key is: " + datainfo + "\n");
            #print("Data is: " + str(data[datainfo]) + "\n");
            #print("Key [:5] is: " + datainfo.lower()[:6] + "\n");
            if(course_name in datainfo.lower()[:6]):
                #print("Found: " + course_name);
                #print("Description: " + data[datainfo]["courseDescription"])
                #print("Title: " + data[datainfo]["courseTitle"])
                totalReturn = "Title: " + data[datainfo]["courseTitle"] + "\n\n" + "Description: " + data[datainfo]["courseDescription"] + "\n\n"
                return(totalReturn)
    return ''

def IncrementCourse(course_name, item_id):
    request = db.child(CourseDb).get();

    found = False;
    #Course Exists in db
    if(not isServiced(item_id)):
        if(request and request.each() is not None):
            for course in request.each():
                print("courseKey: " + course.key());
                print("courseVal: ");
                print(course.val());
                if(course.val()['courseKey'] == course_name):
                    count = course.val()['courseCount'];
                    countInt = int(count) + 1;
                    payload = { "courseKey": course_name, "courseCount": str(countInt) }
                    db.child(CourseDb).child(course.key()).update(payload)
                    found = True;
                    print("Found course: " + course_name + " Now hit: " + str(countInt))
                    break;
        if(not found):
            payload = { "courseKey": course_name, "courseCount": "1" }
            db.child(CourseDb).push(payload);
            print("added new course: " + course_name);
        updateServiced(item_id)

def getOverallCourseHits(course_name):
    reply = "";
    request = db.child(CourseDb).get();
    countHitsForCourse = 0;
    totalCount = 0;
    if(request and request.each() is not None):
        for course in request.each():
            if(course.val()['courseKey'] == course_name):
                countHitsForCourse = int(course.val()['courseCount'])
            totalCount = totalCount + int(course.val()['courseCount'])
            reply = reply + "Course: " + course.val()['courseKey'] + "  /  Total Hits: " + course.val()['courseCount'] + "\n\n"
    if(totalCount > 0):
        reply = reply + "\n\nTotal hits for specific course -- " + course_name + " is: " + str(countHitsForCourse);
        reply = reply + "\n\n" + "This course accounts for " + str(float((float)(float(countHitsForCourse)/float(totalCount)))*100) + "%" + " of all hits." + "\n\n"
        reply = reply + "\n\n Total times I have been referenced to hit courses: " + str(totalCount)
    return(reply);



# Check submissions and comments for course names and reply accordingly
def checkItem(item):
    skip = False
    try:
        course_mentioned = re.findall(COURSE_NAME_REGEX, item.title)
        lower_title = item.title.lower()
        #if 'grade' in lower_title or 'mark' in lower_title:
        #    skip = True
        skip = True
    except AttributeError:
        course_mentioned = re.findall(COURSE_NAME_REGEX, item.body)
    #setFalse(item.id)
    if len(course_mentioned) == 1 and not isServiced(item.id) and not item.author.name == courseBotName:
        #print("We matched: " + item.body)
        if skip:
            print("Printing item title: " + item.title)
        else:
            print("Printing item body: " + item.body)
        print("Not serviced: " + item.author.name);
        course_name = course_mentioned[0]
        if(len(course_name) > 6):
            courseInner = re.findall(re.compile(r'[a-zA-Z]{3}[0-9]{3}'), course_mentioned[0])
            if(len(courseInner) > 0):
                course_name = courseInner[0];
        #reply = getCourseInfo(course_name.lower())
        #print("courseNameMatched: " + course_name)
        #reply = "hello world"
        #reply = getCourseInfo(course_name)
        IncrementCourse(course_name, item.id)
        reply = getOverallCourseHits(course_name);
        replyCourseDescription = getCourseInfo(course_name)
        if reply and not skip:
            reply = reply + '\n\n'
            pre = '###' + course_name.upper() + ':\n\n'
            if(replyCourseDescription == ''):
                reply = pre + reply
            else:
                reply = pre + "\n" + replyCourseDescription + "\n" + reply
            try:
                item.reply(reply)
            except:
                sleep(5)
                return
            print(reply)

        if reply and skip:
            reply = reply + '\n\n'
            pre = '###' + course_name.upper() + ':\n\n'
            if(replyCourseDescription == ''):
                reply = pre + reply
            else:
                reply = pre + "\n" + replyCourseDescription + "\n" + reply
            try:
                item.add_comment(reply)
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
    subreddit_submissions = subreddits.new(limit=25)
    for comment in subreddit_comments:
        #print("Comment Author: " + comment.author.name)
        #print("Comment Body: " + comment.body)
        checkItem(comment)
    for submission in subreddit_submissions:
        checkItem(submission)

# Log in once
r = login()

# Every 5 minutes, scan subreddits and comments for matches and act accordingly
while True:
    run(r)
    sleep(300)