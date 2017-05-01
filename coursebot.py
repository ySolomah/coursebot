#!/usr/bin/python3
import praw
import re

def login():
	r = praw.Reddit(username = config.username,
				password = config.password,
				client_id = config.client_id,
				client_secret = config.client_secret,
				user_agent = "CourseBot v0.1")
	return r

def commentIsServiced(comment_id):
	#update db here

def isCommentServiced(comment_id):
	#check db here

def getCourseInfo(course_name):
	#return course info

def run(r):
	subreddit = r.get_subreddit('uoft+dcs_uoft')
	subreddit_comments = subreddit.get_comments()
	course_regex = re.compile(r'\s[a-zA-Z]{3}\d{3}\s')
	for comment in subreddit_comments:
		course_mentioned = course_regex.search(comment.body)
	    if course_mentioned and not isCommentServiced(comment.id):
	        comment.reply(getCourseInfo(course_mentioned.group(0)))
	        commentIsServiced(comment.id)

r = login()
run(r)