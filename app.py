import re
import string
from collections import Counter
import os

import numpy as np
import pandas as pd
import requests
import spotipy
from bs4 import BeautifulSoup
from googlesearch import search
from spotipy.oauth2 import SpotifyOAuth

import constants

def main():
    print('started app!')

    #connect to Spotify account using OAuth, virtual env, and environment vars
    username = 'arnavakula'
    scope = 'user-modify-playback-state user-read-recently-played streaming user-top-read playlist-modify-public user-read-playback-position user-library-read'
    token = SpotifyOAuth(username=username, scope=scope)

    #create spotify object to access api
    spot = spotipy.Spotify(auth_manager=token)

    #connect to genius api
    genius_access_token = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN')
    genius_header = {'Authorization': f'Bearer {genius_access_token}'}

    #create dataframe to store track info
    df = pd.DataFrame(columns=['TRACK', 'ARTISTS', 'RELEASE_DECADE', 'GENRE', 'LYRICS'])

    #clear file and add columns
    df.to_csv('songs.csv', index=False)

    offset = 0

    while True:
        #get the track
        saved_tracks = spot.current_user_saved_tracks(1, offset=offset) #735 saved songs as of 7/10/2022
        
        print('song %i' %offset)

        try:
            uri = saved_tracks['items'][0]['track']['uri']
        except:
            print('COULD NOT GET SAVED TRACK FOR SONG %i' %offset)
            quit()

        track_name = spot.track(uri)['name'] 
        artist_names = []

        id = ''
        artist_name = ''
        genre_words = set()
        album_artist = spot.track(uri)['album']['artists'][0]['name'].lower()

        #get genres
        for artist in spot.track(uri)['artists']:
            id = artist['id']
            artist_name = artist['name']

            artist_names.append(artist_name)
            
            genres = ' '.join(spot.artist(id)['genres'])

            #combine hip hop into one word 
            genres = re.sub('hip hop', 'hip-hop', genres).split(' ')

            counter = Counter(genres)

            #get all unique genres
            for genre in counter.most_common(constants.GENRE_COUNT):
                genre_words.add(genre[0])

        #get search parameters
        search_param = remove_punctuation(track_name).lower()
        search_param = re.sub('feat.*', '', search_param)
        search_param = re.sub(' ', '-', (search_param + ' ' + album_artist))
        print(search_param)
        
        #format url
        search_url = "http://api.genius.com/search?q='{}'".format(search_param)

        #send request
        req = requests.get(search_url, headers=genius_header)
        try:
            url = req.json()['response']['hits'][0]['result']['url']
            release_decade = get_release_decade(str(req.json()['response']['hits'][0]['result']['release_date_components']['year']))
            lyrics = get_lyrics(url)


            for g in genre_words:
                temp = pd.DataFrame(index=range(1), columns=['TRACK', 'ARTISTS', 'RELEASE_DECADE', 'GENRE', 'LYRICS'])
                temp['TRACK'] = track_name
                temp['ARTISTS'] = str(artist_names)
                temp['LYRICS'] = lyrics
                temp['GENRE'] = g
                temp['RELEASE_DECADE'] = release_decade

                with open('songs.csv', 'a') as f:
                   f.write(temp.to_csv(index=False, index_label=False, header=False))
                

        except Exception as e:
            print()
            print(repr(e))
            print(req.json())
            print('COULDNT FIND FOR:', track_name, 'by:', artist_names)
            print()
        
        offset += 1

#scrape genius.com for lyrics and format them  
def get_lyrics(url):
    result = requests.get(url)
    soup = BeautifulSoup(result.text, 'html.parser')        

    result.close()

    lyrics = ''

    for tag in soup.select('div[class^="Lyrics__Container"], .song_body-lyrics p'):
        t = tag.get_text(strip=True, separator='\n')
        if t:
            lyrics += t

    #remove new lines and bracketed text (usually artist names)
    lyrics = re.sub('\n', ' ', lyrics)
    lyrics = re.sub('\[.*?\]', '', lyrics)

    lyrics = remove_punctuation(lyrics)

    #lower case and unicode encoding
    lyrics = lyrics.lower().encode('utf-8')

    return lyrics
    
def remove_punctuation(str):
    return ''.join([char for char in str if char not in string.punctuation])

def get_release_decade(year):
    return year[0:3] + '0s'
    
    
    
    #vectorize lyrics with tfidf
    #keep on adding genres as labels
    #features = audio features, transformed lyrics

    #TODO use year of release to categorize songs (2020s, 2010s, oldie)
    #TODO try to use artist of album OR most popular artist OR iterative algorithm of artist combinations to search for song
    #TODO check computation time of storing in a df and writing to csv OR storing as a series and repeatedly adding to an 'a' file



if __name__ == '__main__':
    main()
