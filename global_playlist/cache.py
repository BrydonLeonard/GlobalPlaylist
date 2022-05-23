from global_playlist.data_types import Playlist, ClientToken
from datetime import datetime
from decimal import Decimal

class DDBCache:
    PLAYLIST_TABLE = 'GlobalPlaylist-Playlists'
    # An entire table for a single token is slight overkill, but this leaves
    # the door open for supporting multiple users in future.
    TOKEN_TABLE = 'GlobalPlaylist-Tokens'
    CONFIG_TABLE = 'GlobalPlaylist-Config'

    CLIENT_TOKEN_ID="client_token"

    def __init__(self, ddb_resource):
        """
        :param ddb_resource: A boto3 DDB resource object
        """
        self.ddb_resource = ddb_resource
        self.playlist_table = ddb_resource.Table(self.PLAYLIST_TABLE)
        self.token_table = ddb_resource.Table(self.TOKEN_TABLE)
        self.config_table = ddb_resource.Table(self.CONFIG_TABLE)

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