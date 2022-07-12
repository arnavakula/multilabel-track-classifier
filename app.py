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

    with open('songs.csv', 'w') as f:
        f.write(', '.join(constants.COLUMNS))

    offset = 0

    while True:
        #get the track
        saved_tracks = spot.current_user_saved_tracks(1, offset=offset) #735 saved songs as of 7/10/2022
        
        print('song %i' %offset)

        try:
            song_id = saved_tracks['items'][0]['track']['id']
        except:
            print('COULD NOT GET SAVED TRACK FOR SONG %i' %offset)
            quit()

        track_name = spot.track(song_id)['name']     
        album_artist = spot.track(song_id)['album']['artists'][0]['name'].lower()

        #get search parameters
        search_param = remove_punctuation(track_name).lower()
        search_param = re.sub('feat.*', '', search_param)
        search_param = re.sub('with.*', '', search_param)
        search_param = re.sub('Remastered.*', '', search_param)
        search_param = re.sub(' ', '-', (search_param + ' ' + album_artist))
        
        #format search url 
        search_url = "http://api.genius.com/search?q='{}'".format(search_param)

        #send request
        req = requests.get(search_url, headers=genius_header)
        try:
            url = req.json()['response']['hits'][0]['result']['url']
            release_year = str(req.json()['response']['hits'][0]['result']['release_date_components']['year'])
            release_decade = get_release_decade(release_year)
            lyrics = get_lyrics(url)

            #get genres
            artist_names = []
            genres = get_genres(spot, song_id, artist_names)

            audio_features = spot.audio_features(song_id)

            for g in genres:
                temp = pd.DataFrame(index=range(1))

                #id
                temp['ID'] = song_id
                temp['TRACK_NAME'] = track_name
                temp['ARTISTS'] = str(artist_names)

                #features
                temp['LYRICS'] = lyrics
                temp['DANCEABILITY'] = audio_features[0]['danceability']
                temp['ENERGY'] = audio_features[0]['energy']
                temp['KEY'] = audio_features[0]['key']
                temp['LOUDNESS'] = audio_features[0]['loudness']
                temp['MODE'] = audio_features[0]['mode']
                temp['SPEECHINESS'] = audio_features[0]['speechiness']
                temp['ACOUSTICNESS'] = audio_features[0]['acousticness']
                temp['INSTRUMENTALNESS'] = audio_features[0]['instrumentalness']
                temp['LIVENESS'] = audio_features[0]['liveness']
                temp['VALENCE'] = audio_features[0]['valence']
                temp['TEMPO'] = audio_features[0]['tempo']

                #targets
                temp['GENRE'] = g
                temp['RELEASE_YEAR'] = release_year
                temp['RELEASE_DECADE'] = release_decade

                with open('songs.csv', 'a') as f:
                   f.write(temp.to_csv(index=False, index_label=False, header=False))
                

        except Exception as e:
            print()
            print(repr(e))
            print('COULDNT FIND FOR:', track_name, 'by:', artist_names)
            print()
        
        offset += 1

def get_genres(spot, song_id, artist_names):
    genre_words = set()

    for artist in spot.track(song_id)['artists']:
            id = artist['id']
            artist_names.append(artist['name'])
            
            genres = ' '.join(spot.artist(id)['genres'])

            #combine hip hop into one word 
            genres = re.sub('hip hop', 'hip-hop', genres).split(' ')

            counter = Counter(genres)

            #get all unique genres
            for genre in counter.most_common(constants.GENRE_COUNT):
                genre_words.add(genre[0])
    
    return  genre_words


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
