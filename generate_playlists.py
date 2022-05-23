from global_playlist.spotify_client import SpotifyClient
from global_playlist.song_provider import SongProvider
from global_playlist.playlist_manager import PlaylistManager
import boto3

client = boto3.client('dynamodb')

API_ID = '91a3f5258fb84a5da061f47350562f40'
API_SECRET = '<nope>'

def lambda_handler(event, context):
    client = SpotifyClient(API_ID, API_SECRET)
    song_provider = SongProvider(client, client.get_countries())
    playlist_manager = PlaylistManager(client)

    songs = song_provider.get_random_global_songs(40)

    playlist_manager.create_global_playlist(songs)    

if __name__ == "__main__":
    lambda_handler(None, None)
    # print(client.list_tables())
