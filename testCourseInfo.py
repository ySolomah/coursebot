#!/usr/bin/env python
import praw
import pyrebase
import re
import requests
import json
from bs4 import BeautifulSoup
from config import firebase, reddit
from time import sleep

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
            print("Key is: " + datainfo + "\n");
            #print("Data is: " + str(data[datainfo]) + "\n");
            print("Key [:5] is: " + datainfo.lower()[:6] + "\n");
            if(course_name in datainfo.lower()[:6]):
                print("Found: " + course_name);
                print("Description: " + data[datainfo]["courseDescription"])
                print("Title: " + data[datainfo]["courseTitle"])
                totalReturn = "Title: " + data[datainfo]["courseTitle"] + "\n" + "Description: " + data[datainfo]["courseDescription"] + "\n"
                return(totalReturn)


    return ''

returnedString = getCourseInfo("vis111")
if(returnedString == ""):
    print("String is empty")
print("Returned: " + returnedString)
