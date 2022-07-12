import spotipy
from spotipy.oauth2 import SpotifyOAuth #authenticate user
import json #for data formatting and storage

# scope = 'playlist-modify-public'
username = 'arnavakula'

token = SpotifyOAuth(username=username, scope="user-library-read")

#create object to manipulate api
spot = spotipy.Spotify(auth_manager=token)

#create playlist
# spot.user_playlist_create(user=username, name='automated playlist', public=True, description='generated from practice venv')

#get all playlists
playlists = spot.user_playlists(username)

current_saved_tracks = spot.current_user_saved_tracks()

print(type(current_saved_tracks))

audio_analysis_dict = spot.audio_analysis('6BQNJ0JFKh8sWjQLI6Zudi')['track']
# audio_analysis_dict.pop('codestring')
# audio_analysis_dict.pop('echoprintstring')
# audio_analysis_dict.pop('synchstring')
# audio_analysis_dict.pop('rhythmstring')


print(audio_analysis_dict)


audio_features_dict = spot.audio_features('6BQNJ0JFKh8sWjQLI6Zudi')
print(audio_features_dict)

print(spot.current_user(), '\n')

print(spot.current_user_saved_albums().keys())

#(['meta', 'track', 'bars', 'beats', 'sections', 'segments', 'tatums'])
# print(spot.audio_features('6BQNJ0JFKh8sWjQLI6Zudi'))

#TODO set execution policy to restricted in powershell