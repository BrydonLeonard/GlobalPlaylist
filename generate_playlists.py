from global_playlist.spotify_client import SpotifyClient
from global_playlist.song_provider import SongProvider
from global_playlist.playlist_manager import PlaylistManager
import boto3
from global_playlist.data_types import ConfigKeys
from global_playlist.cache import DDBCache

def lambda_handler(event, context):
    cache = DDBCache(boto3.resource('dynamodb'))

    config = cache.load_app_config()

    if not (ConfigKeys.APP_ID in config and ConfigKeys.APP_SECRET in config):
        raise Exception(f"The app credentials are not configured correctly. \
            Set the {ConfigKeys.APP_ID} and {ConfigKeys.APP_SECRET} keys")

    client = SpotifyClient(config[ConfigKeys.APP_ID], config[ConfigKeys.APP_SECRET], cache)
    song_provider = SongProvider(client, client.get_countries(), cache)
    playlist_manager = PlaylistManager(client)

    songs = song_provider.get_random_global_songs(2)

    playlist_manager.create_global_playlist(songs)    

if __name__ == "__main__":
    lambda_handler(None, None)
