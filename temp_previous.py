import re
import string
from collections import Counter

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

    #create dataframe to store track info
    df = pd.DataFrame(columns=['TRACK', 'ARTISTS', 'GENRE', 'LYRICS'])

    #store all liked (saved) songs
    offset = 0

    while True:
        try:
            saved_tracks = spot.current_user_saved_tracks(limit=constants.LIM_TRACKS, offset=offset) #735 saved songs as of 7/10/2022
        except:
            print('COULD NOT GET SAVED TRACKS')
            quit()
        
        for i in range(offset, len(saved_tracks['items'])):
            try:
                print('song %i' %i)
                uri = saved_tracks['items'][i]['track']['uri']
            except:
                df.to_csv('songs.csv', index=False)
                quit()

            track_name = spot.track(uri)['name'] 
            artist_names = []

            id = ''
            artist_name = ''
            genre_words = set() 

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

            #find azlyrics link for song
            query = track_name
            for artist in artist_names:
                query += ' ' + artist

            query += ' azlyrics'
            results = search(query, tld="co.in", num=5, stop=10, pause=2)
            url = ''

            for link in results:
                if 'azlyrics' in link:
                    url = link
                    break
            
            try:
                #scrape webpage and get lyrics
                result = requests.get(url)
                soup = BeautifulSoup(result.content, 'html.parser')
                result.close()

                tag = soup.find('div', {'class': 'ringtone'}).find_next_sibling('div')
                lyrics = tag.text

                #format lyrics - remove punctation
                lyrics = re.sub('\n', ' ', lyrics)
                lyrics = re.sub('\[.*?\]', ' ', lyrics)
                lyrics = ''.join([char for char in lyrics if char not in string.punctuation])

                #add content to dataframe
                for g in genre_words:
                    df.loc[df.shape[0]] = [np.nan, np.nan, np.nan, np.nan]
                    df.iloc[-1]['TRACK'] = track_name
                    df.iloc[-1]['ARTISTS'] = artist_names
                    df.iloc[-1]['LYRICS'] = lyrics
                    df.iloc[-1]['GENRE'] = g
            except:
                print('NO VALID LINK')
                print('URL: ', url)
                print('TRACK NAME:', track_name)
            
        offset += 50
    
    
    
    #vectorize lyrics with tfidf
    #keep on adding genres as labels
    #features = audio features, transformed lyrics

    #TODO use year of release to categorize songs (2020s, 2010s, oldie)
    #TODO when scraping content, except to get lyrics from newer version of page



if __name__ == '__main__':
    main()
