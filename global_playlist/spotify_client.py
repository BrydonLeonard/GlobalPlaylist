import requests, base64, json, urllib.parse, os, re
from datetime import datetime, timedelta
from global_playlist.data_types import Song, ClientToken

class SpotifyClient:
    ACCOUNTS_ENDPOINT = 'https://accounts.spotify.com'
    API_ENDPOINT = 'https://api.spotify.com/v1'

    def __init__(self, api_id, api_secret, cache):
        self.api_id = api_id
        self.api_secret = api_secret
        self.countries = None
        self.app_token = None
        self.client_token = None
        self.cache = cache
        self.__country_mapping = SpotifyClient.__iso3166_mapping()
        self.__local_auth_flow()
        self.current_user_id = None

    def get_countries(self, invalidate = False):
        """
        Fetch a map of ISO3166 country code: country name 
        """
        if not self.countries or invalidate:
            markets_response = self.__get_request(
                "/markets"
            )

            markets = json.loads(markets_response)['markets']

            self.countries = [(m, self.__country_mapping[m]) for m in markets if m in self.__country_mapping]
        return dict(self.countries)

    # Returns a maximum of 3 playlists for the given search
    def search_playlists(self, search_string, marketplace, global_creds=False):
        response = self.__get_request(
            "/search",
            [
                ('type', 'playlist'),
                ('q', search_string),
                ('limit', '3'),
                ('market', marketplace)
            ],
            global_creds
        )

        return json.loads(response)['playlists']['items']

    def get_current_user_playlists(self):
        return json.loads(self.__get_request(
            "/me/playlists"
        ))['items']

    def get_playlist_tracks(self, playlist_id):
        response = self.__get_request(
            f"/playlists/{playlist_id}",
            [
                ('fields', 'tracks.items(track(name,id,uri,artists))')
            ]
        )

        return [Song(item['track']['id'], item['track']['name'], item['track']['uri'], [artist['id'] for artist in item['track']['artists']]) for item in json.loads(response)['tracks']['items']]
        
    def get_current_user_id(self):
        if not self.current_user_id:
            response = self.__get_request("/me")
            self.current_user_id = json.loads(response)['id']
        
        return self.current_user_id
    
    # Returns new playlist ID if successful
    def create_playlist_for_current_user(self, name, description):
        print("Creating a new playlist")
        user_id = self.get_current_user_id()
        response = requests.request(
            'POST',
            f"{self.API_ENDPOINT}/users/{user_id}/playlists",
            headers = {
                'Authorization': f"Bearer {self.client_token.token}",
                'Content-Type': 'application/json'
            },
            data = json.dumps({
                    'name': name,
                    'description': description
                }, ensure_ascii=False).encode('utf-8')
        ).text

        return json.loads(response)['id']

    def remove_items_from_playlist(self, playlist_id, songs):
        return self.__mutate_playlist_request(
            'DELETE',
            playlist_id,
            json.dumps({
               'tracks': [{'uri': song.uri} for song in songs]
            })
        )
        
    def add_items_to_playlist(self, playlist_id, songs):
        return self.__mutate_playlist_request(
            'POST',
            playlist_id,
            json.dumps({
                'uris': [song.uri for song in songs],
                'position': '0'
            })
        )


# ---------------- ---------------- ---------------------#
# ----------------     private      ---------------------#
# ---------------- ---------------- ---------------------#

    def __mutate_playlist_request(self, request_type, playlist_id, data):
        return requests.request(
            request_type,
            f"{self.API_ENDPOINT}/playlists/{playlist_id}/tracks",
            headers = {
                'Authorization': f"Bearer {self.client_token.token}",
                'Content-Type': 'application/json'
            },
            data = data
        ).text

    def __get_request(self, path, params = [], use_app_creds=False):
        token = self.client_token.token
        if use_app_creds:
            token = self.app_token
        response = requests.request(
            'GET',
            f"{self.API_ENDPOINT}{path}",
            headers = {
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json'
            },
            params = params
        ).text

        return response

    # TODO: Make this portable by storing somewhere other than a text file
    def __local_auth_flow(self):
        self.app_token = self.__get_token()

        self.client_token = self.cache.load_client_token()

        if (not self.client_token):
            print("Creds cache existed, but was not well formed")
            self.client_token = self.__generate_and_save_new_creds()
            self.cache.save_client_token(self.client_token)
        elif (self.client_token.expires_at < datetime.now()):
            self.client_token = self.__refresh_and_save_new_creds()
            self.cache.save_client_token(self.client_token)
        else:
            print('Found valid cached creds. Using those')

    def __generate_and_save_new_creds(self):
        print("Starting new auth process")
        print("Please follow this link. Once you have, paste the redirect link back here:")
        print(self.__generate_auth_link())
        redirect_link = input("Redirect link:")

        code_matcher = r'http://localhost:8888/callback\?code=(.+?)(?:&.+|$)'

        match = re.match(code_matcher, redirect_link)

        if (not match.lastindex or match.lastindex < 1):
            raise Exception(f"Invalid callback: {redirect_link}")
        else:
            print(f"Using code {match.group(1)}")

        code = match.group(1)

        auth_token_response = self.__request_user_auth_token(code)

        if ('access_token' not in auth_token_response):
            raise Exception(f"Something went wrong while getting client creds. API response: {auth_token_response}")

        return self.__client_token_from_auth_response(auth_token_response)

    def __refresh_and_save_new_creds(self):
        print('No valid cached creds')
        # Creds have expired, so get some new ones
        response = self.__request_refreshed_user_auth_token()

        return self.__client_token_from_auth_response(response)

    def __client_token_from_auth_response(self, response):
        refresh_token = None
        if (self.client_token):
            refresh_token = self.client_token.refresh_token
        if ('refresh_token' in response):
            refresh_token = response['refresh_token']

        expiry_delta = int(response['expires_in'])

        client_token = ClientToken(
            response['access_token'],
            refresh_token,
            # Take 5 seconds off for safety
            datetime.now() + timedelta(seconds=expiry_delta - 5)
        )

        return client_token

    def __generate_auth_link(self):
        url = f"{self.ACCOUNTS_ENDPOINT}/authorize?" + '&'.join([
                f"client_id={self.api_id}",
                "response_type=code",
                "redirect_uri=http://localhost:8888/callback",
                "scope=playlist-read-private playlist-modify-private playlist-modify-public playlist-read-collaborative"
                ])
        return urllib.parse.quote_plus(url, safe=';/?:@&=+$,')

    def __auth_token_request(self, additional_data):
        """
        :param additional_data: A list of key:value tuples that will be sent in the client auth token request
        """
        return self.__validated_json_auth_response(
            requests.request(
                'POST',
                f"{self.ACCOUNTS_ENDPOINT}/api/token",
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded'
                },
                data = [
                    ('client_id', self.api_id),
                    ('client_secret', self.api_secret)
                ] + additional_data
            ).text
        )

    def __request_user_auth_token(self, user_auth_code):
        return self.__auth_token_request([
                ('grant_type', 'authorization_code'),
                ('code', user_auth_code),
                ('redirect_uri', 'http://localhost:8888/callback')
            ])
    
    def __request_refreshed_user_auth_token(self):
        return self.__auth_token_request([
                ('grant_type', 'refresh_token'),
                ('refresh_token', self.client_token.refresh_token)
            ])

    def __get_token(self):
        return self.__auth_token_request([
                ('grant_type', 'client_credentials')
            ])

    def __validated_json_auth_response(self, response):
        """
        Validates an auth response by checking whether it has an access token. Raises an exception if it doesn't

        :param response: The serialized response from the Spotify API
        """
        response_json = json.loads(response)
        if 'access_token' not in response_json:
            raise Exception(f"Something went wro ng while fetching an API token. The response was: {response_json}")
        return response_json

    def __iso3166_mapping():
        with open('./resources/country_mapping.json') as file:
            return json.loads(''.join(file.readlines()))