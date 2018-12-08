import urllib3
import requests
import json
import webbrowser
import string
from newsapi import NewsApiClient
import os
import google.oauth2.credentials
import sqlite3

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow

def nytAPI(searchTerm):
	key = "2c35ef4d117e460b815883dfdc5315ea"
	base_url="http://api.nytimes.com/svc/search/v2/articlesearch.json"
    # fetch data from NYT
	nyt = requests.get(base_url, params = {'q': searchTerm,'api-key': key, 'begin_date': '20181126', 'end_date': '20181202'})
    #return data in the right format
	return nyt.json()['response']['docs']

def newsAPIWallStreetJournal(searchTerm):
	#code partially copied from mattlisiv/newsapi-python
	newsapi = NewsApiClient(api_key='d1ae21356040444bbd1ab524da3e41cd')
	articles = newsapi.get_everything(q = searchTerm, sources='the-wall-street-journal', language = 'en', from_param = '2018-11-26', to = '2018-12-02')
	return articles

def newsAPIBBCNews(searchTerm):
	newsapi = NewsApiClient(api_key='d1ae21356040444bbd1ab524da3e41cd')
	articles = newsapi.get_everything(q = searchTerm, sources='bbc-news', language = 'en', from_param = '2018-11-26', to = '2018-12-02')
	return articles

def youtubeAPI(searchTerm):
	key = 'AIzaSyCQy2M67G1hrjPQFyq1ft7fHxjWgWQiF54'

	# used some code from Pres Nichols at github repository https://github.com/spnichol/youtube_tutorial.git
	YOUTUBE_API_SERVICE_NAME = "youtube"
	YOUTUBE_API_VERSION = "v3"
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=key)
	search = youtube.search().list(q = searchTerm, part = 'snippet', type='video', publishedAfter = '2018-11-26T00:00:00Z', publishedBefore = '2018-12-02T00:00:00Z').execute()
	results = search.get("items", [])
	return results

def dataToDatabase(search1):
	search1 = search1.replace(' ', '_')
	conn = sqlite3.connect('news_data.sqlite')
	cur = conn.cursor()
	cur.execute('CREATE TABLE IF NOT EXISTS '+search1+' ("source" TEXT, "headline" TEXT, "url" TEXT, "published_date" TEXT)')
	nyt_data = nytAPI(search1)
	for news in nyt_data:
		cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('New York Times', news['headline']['main'], news['web_url'], news['pub_date']))
	wsj_data = newsAPIWallStreetJournal(search1)
	for news in wsj_data['articles']:
		cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('The Wall Street Journal', news['title'], news['url'], news['publishedAt']))
	bbc_data = newsAPIBBCNews(search1)
	for news in bbc_data['articles']:
		cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('BBC News', news['title'], news['url'], news['publishedAt']))
	youtube_data = youtubeAPI(search1)
	for video in youtube_data:
		cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('Youtube', video['snippet']['title'], 'https://www.youtube.com/watch?v=' + video['id']['videoId'], video['snippet']['publishedAt']))
	conn.commit()


def createDatabase():
	dataToDatabase('Trump')

createDatabase()

