from twython import Twython, TwythonError
from threading import Timer
import time
from secrets import *
from random import randint

import nltk
from nltk.corpus import PlaintextCorpusReader
from nltk.corpus import cmudict
from nltk.corpus import stopwords

import curses
from curses.ascii import isdigit

from math import exp

import csv
import datetime

import sys

twitter = Twython(APP_KEY, APP_SECRET, OAUTH_TOKEN, OAUTH_TOKEN_SECRET)

adjectives = [
                "another",
                "new",
                "your",
                "my",
                "better"
                ]

articles = ["a", "an", "the"]
noun = ["NN", "NNP", "NNS"]

ignoreWords = [
                "the", 
                "atlanta", 
                "georgia", 
                "atl", 
                "we", 
                "i", 
                "they", 
                "rt", 
                "https", 
                "&amp", 
                "amp", 
                "today", 
                "day",
                "tomorrow", 
                "tonight", 
                "n't",
                "'re",
                "'ll"]

month2Num = {
        'Jan' : "01",
        'Feb' : "02",
        'Mar' : "03",
        'Apr' : "04",
        'May' : "05",
        'Jun' : "06",
        'Jul' : "07",
        'Aug' : "08",
        'Sep' : "09", 
        'Oct' : "10",
        'Nov' : "11",
        'Dec' : "12"
    }

#holds data for all runs within a day. Reset every day
wantNeedDictionaries = []   #collective data for wants and needs and word count together
wantDictionaries = []       #collective data for wants and number of times a want is used
needDictionaries = []       #collective data for needs and number of times a need is used


timesRun = 0     #number of times run in the current day
dayCount = 0     #number of days run



needs = {}     #data for needs and number of times a need is used for this day
wants = {}     #data for wants and number of times a want is used for this day

numTweetsUsed = 0

wantNeed = {} #data for wants and needs and word count together
wordCount = {} #holds data for all the words used in the tweets. The code that uses this is commented out since we are looking at wants and needs only

wantLines = [] #lines to append to wantsList csv
needLines = [] #lines to append to needsList csv

latestTweetID = 0 #store the id of the latest tweet pulled so we know where to pick up from where we were


def wordIsOK(word):
    """
    Checks if a word is worth looking at (it's not a stopword or punctuation, etc.)
    """
    stop = stopwords.words('english')
    if (word.lower() not in stop) and (word[:7] != "//t.co/"):
        if (word.strip(".,:;'()-=+&!@#$%?/\[]{}^*_\"`~") != ""):
            if (len(word.strip(".,:;'()-=+&!@#$%?/\[]{}^*_\"")) != 1):
                if (word.lower() not in ignoreWords):
                    return True
    return False


def getGeocodeTweetWordCount():
    """
    Returns a dictionary of words used in tweets of all the users in the user list and the
    stats of each word (number of times word used and the users who used that word)
    """

    global needs
    global wants

    global numTweetsUsed
    global wantNeed
    global wordCount
    global latestTweetID

    weekAgo = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")   #the date from a week ago (we'll pull tweets til we hit this date)
    weekAgoHit = False                                                                      #tells us if we hit the weekAgo date and can stop
    earliestDate = ""                                                                       #holds the date of the earliest tweet on the current page we're pulling from
    earliestID = 0                                                                          #Id number of the earliest tweet we've pulled from the page
    idList = []                                                                             #store IDs of tweets we've already used

    try:
        tweets = twitter.search(q = "", count = 100, geocode = "33.7490,-84.3880,20mi" )        #Get 100 latest tweets with this geocode (atlanta lat long)
    except:
        time.sleep(15)
        tweets = twitter.search(q = "", count = 100, geocode = "33.7490,-84.3880,20mi" )


    firstTweetTime = tweets["statuses"][0]['created_at'][11:19]
    print(firstTweetTime)

    latestTweetID = tweets["statuses"][0]['id']

    #find out when was half an hour ago
    minute = int(firstTweetTime[3:5])
    if minute < 30:
        hourAgo = [int(firstTweetTime[:2])-1, 60 - (30 - minute)]
    else:
        hourAgo = [int(firstTweetTime[:2]), minute - 30]
    hourAgoHit = False;

    for tweet in tweets["statuses"]:                                                                                            #For each tweet that we have gotten
        if tweet['text'].encode('utf8').decode('utf8')[:2] != "RT":
            tweetDate = tweet['created_at'][-4:] + "-" + month2Num[tweet['created_at'][4:7]] + "-" + tweet['created_at'][8:10]      #Get its date
            
            # if (int(tweetDate[:4]) < int(weekAgo[:4])):                                                                             #Check if it's been written within
            #     print("Hitting year if statement\n")                                                                                #the past week
            #     weekAgoHit = True
            # if (int(tweetDate[5:7]) < int(weekAgo[5:7]) and int(tweetDate[:4]) <= int(weekAgo[:4])):
            #     print("hitting month if statement\n")
            #     weekAgoHit = True
            # if (int(tweetDate[8:10]) < int(weekAgo[8:10]) and int(tweetDate[5:7]) <= int(weekAgo[5:7]) and int(tweetDate[:4]) <= int(weekAgo[:4])):
            #     print("hitting day if statement \n" + weekAgo + " " + tweetDate)
            #     weekAgoHit = True

            # if not weekAgoHit:                                          #If it's within the week
            #     earliestDate = tweetDate                                #Make it the earliest tweet that we've looked at so far
            #     earliestID = tweet['id']
            #     idList.append(tweet['id'])
            #     wordCount = updateWordCount(tweet, wordCount)           #Add its words to the wordCount dictionary
            #     numTweetsUsed = numTweetsUsed + 1
            # else:
            #     break                                                   #Break out of the loop if we've gone past a week

            #check if we've gone past half an hour
            tweetTime = tweet['created_at'][11:19]
            print(tweetTime)
            if int(tweetTime[:2]) <= hourAgo[0] and int(tweetTime[3:5]) <= hourAgo[1]:
                hourAgoHit = True;
            elif tweetTime[:2] == "23" and hourAgo[0] == 0 and int(tweetTime[3:5]) <= hourAgo[1]:
                hourAgoHit = True;


            if not hourAgoHit:
                earliestDate = tweetDate                                #Make it the earliest tweet that we've looked at so far
                earliestID = tweet['id']
                idList.append(tweet['id'])
                wordCount = updateWordCount(tweet, wordCount)           #Add its words to the wordCount dictionary
                numTweetsUsed = numTweetsUsed + 1
            else:
                break

    # weekAgoHit = True
    numPages = 1
    try:                                                            #repeat the process, but with earlier tweets
        # while not weekAgoHit and numPages <= 50:
        while not hourAgoHit:
            tweets = twitter.search(q = "", count = 100, geocode = "33.7490,-84.3880,20mi", max_id = earliestID)    #get tweets made earlier than earliestID
            print("\n\n\n\n\n")
           
            
            for tweet in tweets["statuses"]:
                try:
                    if tweet['id'] not in idList and tweet['text'].encode('utf8').decode('utf8')[:2] != "RT":
                        tweetDate = tweet['created_at'][-4:] + "-" + month2Num[tweet['created_at'][4:7]] + "-" + tweet['created_at'][8:10]
                        
                        # if (int(tweetDate[:4]) < int(weekAgo[:4])):
                        #     print("Hitting year if statement\n")
                        #     weekAgoHit = True
                        # if (int(tweetDate[5:7]) < int(weekAgo[5:7]) and int(tweetDate[:4]) <= int(weekAgo[:4])):
                        #     print("hitting month if statement\n")
                        #     weekAgoHit = True
                        # if (int(tweetDate[8:10]) < int(weekAgo[8:10]) and int(tweetDate[5:7]) <= int(weekAgo[5:7]) and int(tweetDate[:4]) <= int(weekAgo[:4])):
                        #     print("hitting day if statement \n" + weekAgo + " " + tweetDate)
                        #     weekAgoHit = True

                        # if not weekAgoHit:
                        #     earliestDate = tweetDate
                        #     earliestID = tweet['id']
                        #     idList.append(tweet['id'])
                        #     wordCount = updateWordCount(tweet, wordCount)
                        #     numTweetsUsed = numTweetsUsed + 1
                        # else:
                        #     break

                        #check if we've gone past half hour mark
                        tweetTime = tweet['created_at'][11:19]
                        print(tweetTime)
                        if int(tweetTime[:2]) <= hourAgo[0] and int(tweetTime[3:5]) <= hourAgo[1]:
                            hourAgoHit = True;
                        elif tweetTime[:2] == "23" and hourAgo[0] == 0 and int(tweetTime[3:5]) <= hourAgo[1]:
                            hourAgoHit = True;

                        if not hourAgoHit:
                            earliestDate = tweetDate                                #Make it the earliest tweet that we've looked at so far
                            earliestID = tweet['id']
                            idList.append(tweet['id'])
                            wordCount = updateWordCount(tweet, wordCount)           #Add its words to the wordCount dictionary
                            numTweetsUsed = numTweetsUsed + 1
                        else:
                            break
                except Exception as err:
                    print(err)

            numPages = numPages + 1

    except Exception as err:
        print(err)

    print(numTweetsUsed, "tweets in total")

    return wordCount




def updateWordCount(tweet, wordCount):
    """
    Updates the wordCount dictionary as well as the wants and needs dictionaries
    """
    global needs
    global wants

    weekAgo = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")       #the date a week ago
    # tweetList = []
    # userTimeline = twitter.get_user_timeline(screen_name=user, count=200, since=weekAgo)
    
    user = tweet['user']['screen_name'].encode('utf8').decode('utf8')                           #username
    tweetText = tweet['text'].encode('utf8').decode('utf8')                                     #tweet text
    # print("created_at: " + tweet['created_at'])
    tweetDate = tweet['created_at'][-4:] + "-" + month2Num[tweet['created_at'][4:7]] + "-" + tweet['created_at'][8:10]  #Date tweet created
    


    try:
        print(tweetText + " " + tweetDate + " " + user)
    except Exception as err:
        print(err)

    tweetSents = nltk.sent_tokenize(tweetText)

    for sent in tweetSents:

        tweetWords = nltk.word_tokenize(sent)          #A list of the tweet words/punctuation
        tweetPOS = nltk.pos_tag(sent)                  #A list of the tweet words and their Part-of-Speech tag
        

        wordIndex = 0                                           #Start at beginning index of 0

        for word in tweetWords:                                 #for each word in the tweet

            
            if wordIsOK(word) and word.lower() != user.lower(): #Check if its ok and that its not the user's username
                # try:
                #     if word.lower() not in wordCount:           #If the word isn't already in the wordCount dictionary
                #         print("ADDING " + word.lower())
                #         wordCount[word.lower()] = [0,[]];       #add it
                #     else:
                #         print(word.lower() + " already in dict")
                        
       
                #     wordCount[word.lower()][0] = wordCount[word.lower()][0] + 1 #increase the number of times it's been used
                #     if(user not in wordCount[word.lower()][1]):                 #Add the username of user who used the word
                #         wordCount[word.lower()][1].append(user)
                # except Exception as err:
                #     print(err)

                try:
                    updateNeeds(word, wordIndex, tweetWords, tweetPOS, user, tweet['created_at'])
                    updateWants(word, wordIndex, tweetWords, tweetPOS, user, tweet['created_at'])
                except Exception as err:
                    print(err)   

            wordIndex = wordIndex + 1


    return(wordCount)


def updateNeeds(word, wordIndex, tweetWords, tweetPOS, user, tweetDate):
    """
    Updates the dictionary of words that follow "need" in tweets
    word is the current word being looked at in the tweet
    wordIndex is the index of the word
    tweetWords is a list of all the words in the tweet
    tweetPOS is a list of the parts of speech of every word in the tweet 
    user is the name of the user who tweeted
    """
    global needs                                                                                #Get the global variable needs dictionary
    global wantNeed
    global needLines
    if word.lower() == "need" or word.lower() == "needs" or word.lower() == "needed" or word.lower() == "needing":           #If the word is a form of "need"
        if wordIndex + 1 < len(tweetWords) and tweetWords[wordIndex + 1] == "to":               #if it's followed by "to"
            if wordIsOK(tweetWords[wordIndex + 2].lower()):
                try:
                    endIndex = 2
                    addList = ["to", tweetWords[wordIndex + endIndex]]                          #Get the phrase "to [verb]"

                    print("Adding '" + ' '.join(addList).lower() + "' to NEEDS")
                    add = ' '.join(addList).lower()

                    if add not in needs:                                                        #If the phrase isn't already in the needs dictionary
                        needs[add] = [0, []]                                                    #Add it
                    needs[add][0] = needs[add][0] + 1                                           #Increase the number of times the phrase was used
                    if (user not in needs[add][1]):                                             #Add the username to the list of users who have used this phrase
                        needs[add][1].append(user)
                    date = tweetDate[-4:] + "-" + month2Num[tweetDate[4:7]] + "-" + tweetDate[8:10]
                    time = tweetDate[11:19]
                    # needs_csv.writerow([add, user, date, time])
                    needLines.append([add, user, date, time])

                    if add not in wantNeed:
                        wantNeed[add] = ["n",0]
                    elif wantNeed[add][0] == "w":
                        wantNeed[add][0] = "wn"
                    wantNeed[add][1] = wantNeed[add][1] + 1
                except Exception as err:
                    print(err)
        elif wordIndex + 1 < len(tweetWords):
            if wordIsOK(tweetWords[wordIndex + 1].lower())  or tweetWords[wordIndex + 1].lower() in articles or tweetWords[wordIndex + 1].lower() in ignoreWords:       #if there's another word following the "need" word
                try:
                    endIndex = 1
                    addList = [tweetWords[wordIndex + endIndex]]                                #keep adding words to the phrase until you've hit something other than an adj or adv
                    while(wordIndex + endIndex + 1 < len(tweetWords) and ( tweetWords[wordIndex + endIndex].lower() in articles or tweetWords[wordIndex + endIndex] == "and" or not(tweetPOS[wordIndex + endIndex][1] in noun) or tweetWords[wordIndex + endIndex].lower() in adjectives)):
                        
                        endIndex += 1
                        if(tweetWords[wordIndex + endIndex] == "." or tweetWords[wordIndex + endIndex] == "," or tweetWords[wordIndex + endIndex] == "for" or tweetWords[wordIndex + endIndex] == "of" or tweetWords[wordIndex + endIndex] == "https"):
                            break
                        addList.append(tweetWords[wordIndex + endIndex])

                    # addList.append(tweetPOS[wordIndex + endIndex][1])
                    print("Adding '" + ' '.join(addList).lower() + "' to NEEDS")
                    # needs.append(tweetWords[wordIndex + 1].lower())

                    add = ' '.join(addList).lower()

                    if add not in needs:                                #If it isn't already in the dictionary
                        needs[add] = [0, []]                            #add it
                    needs[add][0] = needs[add][0] + 1                   #Increase the number of times it's been used
                    if (user not in needs[add][1]):                     #Add the username to the list of users who have used this phrase
                        needs[add][1].append(user)
                    date = tweetDate[-4:] + "-" + month2Num[tweetDate[4:7]] + "-" + tweetDate[8:10]
                    time = tweetDate[11:19]
                    # needs_csv.writerow([add, user, date, time])
                    needLines.append([add, user, date, time])

                    if add not in wantNeed:
                        wantNeed[add] = ["n",0]
                    elif wantNeed[add][0] == "w":
                        wantNeed[add][0] = "wn"
                    wantNeed[add][1] = wantNeed[add][1] + 1
                except Exception as err:
                    print(err)

def updateWants(word, wordIndex, tweetWords, tweetPOS, user, tweetDate):
    """
    Updates the dictionary of words that follow "want" in a tweet
    word is the current word being looked at in the tweet
    wordIndex is the index of the word
    tweetWords is a list of all the words in the tweet
    tweetPOS is a list of the parts of speech of every word in the tweet 
    user is the name of the user who tweeted
    """

    global wants                                                                            #Get the global variable wants
    global wantNeed
    global wantLines
    # global wants_csv

    if word.lower() == "want" or word.lower() == "wants" or word.lower() == "wanted" or word.lower() == "wanting":       #If the word is a form of "want"
        if wordIndex + 1 < len(tweetWords) and tweetWords[wordIndex + 1] == "to":           #If it's followed by "to"
            if wordIsOK(tweetWords[wordIndex + 2].lower()):
                try:
                    endIndex = 2
                    addList = ["to", tweetWords[wordIndex + endIndex]]                      #Get the phrase "to [verb]"

                    print("Adding '" + ' '.join(addList).lower() + "' to WANTS")
                    add = ' '.join(addList).lower()
                    
                    if add not in needs:                            #If it is not already in the dictionary
                        wants[add] = [0, []]                        #add it
                    wants[add][0] = wants[add][0] + 1               #increment number of times it's been used
                    if (user not in wants[add][1]):                 #If the user isn't already in the list of users who have used the word
                        wants[add][1].append(user)                  #add their username to the list

                    date = tweetDate[-4:] + "-" + month2Num[tweetDate[4:7]] + "-" + tweetDate[8:10]
                    time = tweetDate[11:19]
                    # wants_csv.writerow([add, user, date, time])
                    wantLines.append([add, user, date, time])

                    if add not in wantNeed:
                        wantNeed[add] = ["w",0]
                    elif wantNeed[add][0] == "n":
                        wantNeed[add][0] = "wn"
                    wantNeed[add][1] = wantNeed[add][1] + 1
                except Exception as err:
                    print(err)
        elif wordIndex + 1 < len(tweetWords):                       #Otherwise, add the words following "want"
            if wordIsOK(tweetWords[wordIndex + 1].lower()) or tweetWords[wordIndex + 1].lower() in articles or tweetWords[wordIndex + 1].lower() in ignoreWords:
                try:
                    endIndex = 1
                    addList = [tweetWords[wordIndex + endIndex]]    #Keep adding all the adjectives or other words in the phrase until you hit a noun or something
                    while(wordIndex + endIndex + 1 < len(tweetWords) and (tweetWords[wordIndex + endIndex].lower() in articles or tweetWords[wordIndex + endIndex] == "and" or not(tweetPOS[wordIndex + endIndex][1] in noun) or tweetWords[wordIndex + endIndex].lower() in adjectives)):
                        endIndex += 1
                        if(tweetWords[wordIndex + endIndex] == "." or tweetWords[wordIndex + endIndex] == "," or tweetWords[wordIndex + endIndex] == "for" or tweetWords[wordIndex + endIndex] == "of" or tweetWords[wordIndex + endIndex] == "https"):
                            break
                        addList.append(tweetWords[wordIndex + endIndex])

                    # addList.append(tweetPOS[wordIndex + endIndex][1])
                    print("Adding '" + ' '.join(addList).lower() + "' to WANTS")
                    # needs.append(tweetWords[wordIndex + 1].lower())
 
                    add = ' '.join(addList).lower()

                    if add not in needs:                            #Add word/phrase to the dictionary
                        wants[add] = [0, []]
                    wants[add][0] = wants[add][0] + 1               #And Increment the number of times it's been used
                    if (user not in wants[add][1]):
                        wants[add][1].append(user)                  #Add username to the list of users who have used this word/phrase
                    date = tweetDate[-4:] + "-" + month2Num[tweetDate[4:7]] + "-" + tweetDate[8:10]
                    time = tweetDate[11:19]
                    # wants_csv.writerow([add, user, date, time])
                    wantLines.append([add, user, date, time])

                    if add not in wantNeed:
                        wantNeed[add] = ["w",0]
                    elif wantNeed[add][0] == "n":
                        wantNeed[add][0] = "wn"
                    wantNeed[add][1] = wantNeed[add][1] + 1
                except Exception as err:
                    print(err)



def atlGeocodeTwitterSummary():
    """
    Writes a csv file that outlines the words that were used in ATL tweets
    """

    # tweetWords = getGeocodeTweetWordCount();
    tweetWords = wordCount

    open_csv = open("summaryGeocode" + str(dayCount) + ".csv", "w", newline='')
    summary_csv = csv.writer(open_csv)
    #summary_csv.writerow([str(numTweetsUsed) + " tweets in total"])
    # summary_csv.writerow(["Word", "Number of times used", "Users who used Word"])
    summary_csv.writerow(["Word", "Number of times used"])

    rowsList = []
    for word in tweetWords:
        # usersString = ""
        # for user in tweetWords[word][1]:
        #     usersString = usersString + user + ", "
        # row = [word, tweetWords[word][0], usersString]
        row = [word, tweetWords[word][0]]
        placeFound = False
        currI = 0
        while not placeFound:

            if currI == len(rowsList) or row[1] >= rowsList[currI][1]:
                placeFound = True
                rowsList.insert(currI, row)
            else:
                currI = currI + 1
   
    for row in rowsList:
        try:
            summary_csv.writerow(row)
        except Exception as err:
            print(err)

    open_csv.close()


def writeWantNeed():
    """
    Writes a file that tallies up the number of times a phrase was used
    and whether or not it was used as a want, a need, or both
    """
    open_csv = open("wantNeed" + str(dayCount) + ".csv", "w", newline='')
    summary_csv = csv.writer(open_csv)
    #summary_csv.writerow([str(numTweetsUsed) + " tweets in total"])
    summary_csv.writerow(["Phrase", "W/N", "Number of Uses"])

    for entry in wantNeed:
        summary_csv.writerow([entry, wantNeed[entry][0], wantNeed[entry][1]])

    open_csv.close()


def writeNeedsWantsSummaries():
    """
    Writes individual files for Needs and Wants depicting the phrases for Needs/Wants,
    number of times used, and the users who said them. This overwrites an existing file
    made for the day, updating it with the new data.
    """
    open_csv = open("needsSummary" + str(dayCount) + ".csv", "w", newline='')
    summary_csv = csv.writer(open_csv)
    #summary_csv.writerow([str(numTweetsUsed) + " tweets in total"])
    # summary_csv.writerow(["Needs", "Number of times used", "Users"])
    summary_csv.writerow(["Needs", "Number of times used"])

    rowsList = []
    for word in needs:
        # print(word)
        # usersString = ""
        # for user in needs[word][1]:
        #     usersString = usersString + user + ", "
        # row = [word, needs[word][0], usersString]
        row = [word, needs[word][0]]
        placeFound = False
        currI = 0
        while not placeFound:
            if currI == len(rowsList) or row[1] >= rowsList[currI][1]:
                placeFound = True
                rowsList.insert(currI, row)
            else:
                currI = currI + 1
   
    for row in rowsList:
        try:
            summary_csv.writerow(row)
        except Exception as err:
            print(err)

    open_csv.close()


    open_csv = open("wantsSummary" + str(dayCount) + ".csv", "w", newline='')
    summary_csv = csv.writer(open_csv)
    # summary_csv.writerow(["Wants", "Number of times used", "Users"])
    summary_csv.writerow(["Wants", "Number of times used"])

    rowsList = []
    for word in wants:
        # print(word)
        # usersString = ""
        # for user in wants[word][1]:
        #     usersString = usersString + user + ", "
        # row = [word, wants[word][0], usersString]
        row = [word, wants[word][0]]
        placeFound = False
        currI = 0
        while not placeFound:

            if currI == len(rowsList) or row[1] >= rowsList[currI][1]:
                placeFound = True
                rowsList.insert(currI, row)
            else:
                currI = currI + 1
   
    for row in rowsList:
        try:
            summary_csv.writerow(row)
        except Exception as err:
            print(err)

    open_csv.close()

def appendNeedLines():
    """
    Updates thes needsList csv file that holds a list of all the needs, their time stamps, dates, and user who tweeted them
    """
    newNeedLines = needLines[::-1]
    openNeeds_csv = open("needsList" + str(dayCount) + ".csv", "a", newline='')
    needs_csv = csv.writer(openNeeds_csv)

    for line in newNeedLines:
        needs_csv.writerow(line)

    openNeeds_csv.close()

def appendWantLines():
    """
    Updates thes wantsList csv file that holds a list of all the wants, their time stamps, dates, and user who tweeted them
    """
    newWantLines = wantLines[::-1]
    openWants_csv = open("wantsList" + str(dayCount) + ".csv", "a", newline='')
    wants_csv = csv.writer(openWants_csv)

    for line in newWantLines:
        wants_csv.writerow(line)

    openWants_csv.close()





firstRun = True

def runBot():
    global dayCount
    global timesRun
    global wantNeedDictionaries
    global wantDictionaries
    global needDictionaries

    global needs
    global wants

    global numTweetsUsed
    global wantNeed
    global wordCount

    global firstRun

    global timesRun
    global dayCount

    global wantLines
    global needLines

    if timesRun == 0:

        if not firstRun:
            #append the data of the last run to the cumulative data for the day
            wantNeedDictionaries.append(wantNeed)
            wantDictionaries.append(wants)
            needDictionaries.append(needs)

        firstRun = False

        


        # Reset Everything
        needs = {}
        wants = {}

        numTweetsUsed = 0

        wantNeed = {}
        wordCount = {}

        openWants_csv = open("wantsList" + str(dayCount) + ".csv", "w", newline='')
        wants_csv = csv.writer(openWants_csv)

        openNeeds_csv = open("needsList" + str(dayCount) + ".csv", "w", newline='')
        needs_csv = csv.writer(openNeeds_csv)

        wants_csv.writerow(["Want", "User", "Date", "Time"])
        needs_csv.writerow(["Need", "User", "Date", "Time"])

        openWants_csv.close()
        openNeeds_csv.close()

        

    wantLines = []
    needLines = []

    getGeocodeTweetWordCount()          #update the dictionaries

    # atlGeocodeTwitterSummary()        #this makes a csv file of the entire wordcount from tweets

    writeNeedsWantsSummaries()          #update wantSummary and needSummary csv files
    writeWantNeed()                     #update wantNeed csv file

    

    appendWantLines()
    appendNeedLines()

    


    timesRun = timesRun + 1
    if timesRun == 48:
        timesRun = 0
        dayCount = dayCount + 1

    print("Finished Iteration #" + str(timesRun) + " on day #" + str(dayCount))


def setInterval(func, sec):
    def func_wrapper():
        setInterval(func, sec)
        func()
    t = Timer(sec, func_wrapper)
    t.start()
    return t

runOnce = False
runBot()
if not runOnce:
    setInterval(runBot, 60*30) # runs every 30 minutes
