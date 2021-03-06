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
import csv
import plotly
import plotly.plotly as py 
import plotly.graph_objs as go 
import API_credentials



def nytAPI(searchTerm):
	"""Retrieves data from New York Times API
	Input: searchterm to be the query parameter for NYT API
	Returns list of items, each representing an article that is found within the parameters given to the API
	"""
	key = API_credentials.nyt_key
	base_url="http://api.nytimes.com/svc/search/v2/articlesearch.json"
    # fetch data from NYT
	nyt = requests.get(base_url, params = {'q': searchTerm,'api-key': key, 'begin_date': '20181126', 'end_date': '20181202'})
    #return data in the right format
	return nyt.json()['response']['docs']

def newsAPIWallStreetJournal(searchTerm):
	"""Retrieves data from the Wall Street Journal using the Google News API
	Input: searchterm that is used as the query parameter for the News API
	Returns a list of articles that are found within the parameters giving to the API
	"""
	#code partially copied from mattlisiv/newsapi-python
	newsapi = NewsApiClient(api_key=API_credentials.newsAPI_key)
	articles = newsapi.get_everything(q = searchTerm, sources='the-wall-street-journal', language = 'en', from_param = '2018-11-26', to = '2018-12-02')
	return articles

def newsAPIBBCNews(searchTerm):
	"""Retrieves data from BBC News using the Google News API (same API as newsAPIWallStreetJournal)
	Input: searchterm that is used as the query parameter for the News API
	Returns a list of articles that are found within the parameters giving to the API
	"""
	newsapi = NewsApiClient(api_key=API_credentials.newsAPI_key)
	articles = newsapi.get_everything(q = searchTerm, sources='bbc-news', language = 'en', from_param = '2018-11-26', to = '2018-12-02')
	return articles

def youtubeAPI(searchTerm):
	"""Retrives data from Youtube using the Youtube API
	Input: a seachTerm that is used as the query parameter for the API
	Returns a list of video items that are found within the parameters given to the API
	"""
	key = API_credentials.youtube_key
	# used some code from Pres Nichols at github repository https://github.com/spnichol/youtube_tutorial.git
	YOUTUBE_API_SERVICE_NAME = "youtube"
	YOUTUBE_API_VERSION = "v3"
	youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=key)
	search = youtube.search().list(q = searchTerm, part = 'snippet', type='video', publishedAfter = '2018-11-26T00:00:00Z', publishedBefore = '2018-12-02T00:00:00Z').execute()
	results = search.get("items", [])
	return results

def createDatabaseConnection(databaseName):
	"""Creates connection to SQL database
	If connection successful, return connection object
	Otherwise, prints error message
	"""
	#taken from http://www.sqlitetutorial.net/sqlite-python/sqlite-python-select/
	try:
		conn = sqlite3.connect(databaseName)
		return conn
	except Error as e:
		print(e)

def dataToDatabase(search1, conn):
	"""Retrives data from all four APIs by calling respective functions
	Input: searchterm to be searched on all four sources, database connection
	Creates a cursor, creates table named after the searchterm
	Executes adding each piece of data to table without duplictae items
	"""
	cur = conn.cursor()
	if ((search1 != 'None') and (search1 != '')):
		search1 = search1.replace(' ', '_')
		cur.execute('CREATE TABLE IF NOT EXISTS '+search1+' ("source" TEXT, "headline" TEXT, "url" TEXT, "published_date" TEXT)')
		nyt_data = nytAPI(search1)
		for news in nyt_data:
			cur.execute('SELECT headline FROM '+search1+' WHERE url = ? LIMIT 1', (news['web_url'], ))
			if cur.fetchone():
				print('NYT article in database')
			else:
				cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('New York Times', news['headline']['main'], news['web_url'], news['pub_date']))
		wsj_data = newsAPIWallStreetJournal(search1)
		for news in wsj_data['articles']:
			cur.execute('SELECT headline FROM '+search1+' WHERE url = ? LIMIT 1', (news['url'], ))
			if cur.fetchone():
				print('WSJ article in database')
			else:
				cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('The Wall Street Journal', news['title'], news['url'], news['publishedAt']))
		bbc_data = newsAPIBBCNews(search1)
		for news in bbc_data['articles']:
			cur.execute('SELECT headline FROM '+search1+' WHERE url = ? LIMIT 1', (news['url'], ))
			if cur.fetchone():
				print('BBC article in database')
			else:
				cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('BBC News', news['title'], news['url'], news['publishedAt']))
		youtube_data = youtubeAPI(search1)
		for video in youtube_data:
			cur.execute('SELECT headline FROM '+search1+' WHERE url = ? LIMIT 1', ('https://www.youtube.com/watch?v=' + video['id']['videoId'], ))
			if cur.fetchone():
				print('Youtube video in database')
			else:
				cur.execute('INSERT INTO '+search1+' (source, headline, url, published_date) VALUES (?, ?, ?, ?)', ('Youtube', video['snippet']['title'], 'https://www.youtube.com/watch?v=' + video['id']['videoId'], video['snippet']['publishedAt']))
		conn.commit()

def createDataDict(conn):
	"""Creates dictionary of number of stories by source and searchterm/tablename by looping through each table in database
	Input: database connection object
	Returns dictionary with searchterm/table name as keys, with dictionary with sources and number of stories for the week as values
	"""
	cur = conn.cursor()
	cur.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
	x = cur.fetchall()
	tables = []
	for table in x:
		tables += [table[0]]
	graphDict = {}
	for table in tables:
		cur.execute('SELECT source FROM '+table)
		tableData = []
		for item in cur.fetchall():
			tableData += [item[0]]
		graphDict[table] = {}
		for item in tableData:
			if item not in graphDict[table]:
				graphDict[table][item] = 0
			graphDict[table][item] += 1
	return graphDict

def createCSVReport(dataDict):
	""" Writes csv file with counted results
	Input: dictionary created in createDataDict
	"""
	outfile = open("newsData.csv", "w")
	writer = csv.writer(outfile)
	myFields = ['topic/search', 'source', 'count']
	writer.writerow(myFields)
	for topic in list(dataDict.keys()):
		for source in dataDict[topic]:
			writer.writerow([topic, source, dataDict[topic][source]])
	outfile.close()

def createPlotlyBarChart(dataDict):
	"""Creates plotly bargraph and sends it to my Plotly account
	Input: data dictionary with {searchterm: {source: number of stories}
	Output: bargraphs by searc, with representation of the number of stories from each source
	If there are no stories from the source on that search, it is still represented with a zero
	"""
	plotly.tools.set_credentials_file(username=API_credentials.plotly_username, api_key=API_credentials.plotly_api_key)
	x = list(dataDict.keys())
	sources = list(dataDict[x[0]].keys())
	barGroups = []
	for source in sources:
		y_s = []
		for item in x:
			if source in dataDict[item].keys():
				y_s += [dataDict[item][source]]
			else:
				y_s += [0]
		barGroups += [go.Bar(x=x, y=y_s, name = source, textposition = 'auto')]
	data = barGroups
	layout = go.Layout(title='Number of News Stories/Videos Published During the Week of November 26, 2018 by Topic', xaxis=dict(title='Topic (or search term used)'), yaxis=dict(title='Number of stories/videos published during the week'))
	fig = go.Figure(data=data, layout=layout)
	py.iplot(fig, filename = 'barchart1')

def tearDown(conn):
	"""Tears down connection to database
	Input is database connection objject
	"""
	conn.close()

conn = createDatabaseConnection('news_data.sqlite')
dataToDatabase(input('Search:'), conn)
dataDictionary = createDataDict(conn)
createCSVReport(dataDictionary)
createPlotlyBarChart(dataDictionary)
tearDown(conn)

