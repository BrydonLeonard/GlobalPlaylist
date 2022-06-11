from global_playlist.data_types import Playlist, ClientToken
from datetime import datetime
from decimal import Decimal

class DDBCache:
    PLAYLIST_TABLE = 'GlobalPlaylist-Playlists'
    # An entire table for a single token is slight overkill, but this leaves
    # the door open for supporting multiple users in future.
    TOKEN_TABLE = 'GlobalPlaylist-Tokens'
    CONFIG_TABLE = 'GlobalPlaylist-Config'
    SONG_HISTORY_TABLE = 'GlobalPlaylist-SongHistoryTable'

    CLIENT_TOKEN_ID="client_token"

    def __init__(self, ddb_resource):
        """
        :param ddb_resource: A boto3 DDB resource object
        """
        self.ddb_resource = ddb_resource
        self.playlist_table = ddb_resource.Table(self.PLAYLIST_TABLE)
        self.token_table = ddb_resource.Table(self.TOKEN_TABLE)
        self.config_table = ddb_resource.Table(self.CONFIG_TABLE)
        self.song_history_table = ddb_resource.Table(self.SONG_HISTORY_TABLE)

    def load_app_config(self):
        playlist_scan_response = self.config_table.scan(
            Select='ALL_ATTRIBUTES'
        )

        return dict([(i['key'], i['value']) for i in playlist_scan_response['Items']])

    def load_client_token(self):
        token_get_response = self.token_table.get_item(
            Key={
                'id': self.CLIENT_TOKEN_ID
            }
        )

        if 'Item' in token_get_response:
            token_item = token_get_response['Item']
            return ClientToken(
                token_item['token'],
                token_item['refresh_token'],
                datetime.fromtimestamp(token_item['expires_at'])
            )

        return None
    
    def save_client_token(self, token):
        self.token_table.put_item(
            Item={
                'id': self.CLIENT_TOKEN_ID,
                'token': token.token,
                'refresh_token': token.refresh_token,
                'expires_at': Decimal(token.expires_at.timestamp())
            }
        )

    def load_playlists(self):
        """
        Retrieves a list of playlists from the cache.
        """
        playlist_scan_response = self.playlist_table.scan(
            Select='ALL_ATTRIBUTES'
        )

        playlists = []

        for playlist_item in playlist_scan_response['Items']:
            playlists.append(Playlist(
                playlist_item['id'],
                playlist_item['name'],
                playlist_item['owner'],
                playlist_item['country_id']
            ))

        return playlists

    def save_playlists(self, playlists):
        """
        Takes a list of playlists and upserts them into the playlist cache.
        """
        with self.playlist_table.batch_writer() as batch:
            for playlist in playlists:
                batch.put_item(
                    Item={
                        'country_id': playlist.country_id,
                        'id': playlist.id,
                        'name': playlist.name,
                        'owner': playlist.owner
                    }
                )

    def load_used_songs(self):
        """
        Loads the list of previously used songs.
        :return A list of song Ids
        """
        scan_result= self.song_history_table.scan(
            Select='SPECIFIC_ATTRIBUTES',
            ProjectionExpression = 'id'
        )['Items']

        return [song['id'] for song in scan_result]



    def add_used_songs(self, songs):
        """
        Saves a list of songs so that they won't be used again
        """
        iso_date_string = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            
        with self.song_history_table.batch_writer() as batch:
            for song in songs:
                batch.put_item(
                    Item={
                        'id': song.id,
                        'used_date': iso_date_string,
                        # The info below isn't really _useful_, but it makes it easier to read the database items (manually)
                        'name': song.name,
                        'artists': ','.join(song.artist_names)
                    }
                )