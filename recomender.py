#!/#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import imdb
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import urllib.request
from twilio.rest import Client
from tabulate import tabulate
import logging
import datetime

# Set up logging
logging.basicConfig(filename='movie_scraper.log', level=logging.INFO)

# Log when the code started running
logging.info(f'Code started running at {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')


ia = imdb.IMDb()

# Set up your Twilio account
account_sid = 'ACcf747aac8a00c40c4337cd9811840373'
auth_token = 'a18fe1fbf64e8ad2ed1072c2b42d8cd0'
client = Client(account_sid, auth_token)

movies = pd.read_csv('Movies.csv' )

page = 1
movies_list = []

while True:
    url = 'https://nzdworld.com/category/movies/'
    
    response = requests.get(url)
    
    # Check if the response status code is not 200
    if response.status_code != 200:
        logging.error(f'Response status code: {response.status_code}. Breaking out of loop.')
        break
    
    # Make the request to the website and parse the HTML
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all <h3> tags with class "entry-title"
    h3_tags = soup.select('.entry-title')
    
    # Create an empty list to store the movie names and release dates
    # Loop through the <h3> tags and extract the nested <a> tag
    for h3_tag in h3_tags:
        a_tag = h3_tag.find('a')
        href = a_tag['href']
        text = a_tag.text
        if 'MOVIE' in text:  # Filter out TV series
            movie_text = text.split(':')[-1].strip()  # Extract movie name
            movie_name = movie_text.rsplit('(', 1)[0].strip()  # Remove release date from movie name
            release_date = movie_text.rsplit('(', 1)[1].replace(')', '')  # Extract release date
            
            response = requests.get(str(href))
            soup = BeautifulSoup(response.content, 'html.parser')
            a_tag = soup.find('a', text='DOWNLOAD MOVIE')
            link = a_tag.get('href')

            # Getting movie rating
            search_results = ia.search_movie(str(movie_name))
            
            # Get the first search result (assuming it's the correct movie)
            movie_id = search_results[0].getID()

            # Get the movie details using the ID
            movie = ia.get_movie(movie_id)

            # Get the movie rating
            rating = movie.get('rating')

            movies_list.append([movie_name, release_date, rating,  link])
            
    logging.info(f'Page {page} completed')
    page += 1
    break
    
movies_df = pd.DataFrame(movies_list, columns=['Movie Name', 'Release Date', 'Rating', 'Link'])  

old_movie_names = list(movies['Movie Name'])

# Next, create a list of movie names that are present in the new DataFrame but not in the old DataFrame
new_movie_names = list(set(movies_df['Movie Name']) - set(old_movie_names))

# Create a new DataFrame for the new movies
df_new_movies = movies_df[movies_df['Movie Name'].isin(new_movie_names)]


df = pd.concat([movies, movies_df])
df.drop_duplicates(subset=['Movie Name'], keep='first', inplace=True)
df.to_csv('Movies.csv', index = False)


# In[9]:


df_top5 = df_new_movies.sort_values(['Rating'], ascending = False).head(5)


# In[18]:


# Convert DataFrame to a list of lists
movies_list = df_top5[['Movie Name', 'Rating', 'Link']].values.tolist()

# Format the list of lists using tabulate
movies_text = tabulate(movies_list, headers=['Movie Name', 'Rating', 'Link'])

# Send message via Twilio WhatsApp
message = client.messages.create(
    body=movies_text,
    from_='whatsapp:+14155238886',  # Twilio WhatsApp number
    to='whatsapp:+2349012389795'
)

print('Message sent:', message.sid)


# In[12]:


print(df_top5)


# In[ ]:




