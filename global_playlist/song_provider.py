import os, json, random
from global_playlist.data_types import Playlist

class SongProvider:
    def __init__(self, client, countries, cache, re_cache_playlists = False):
        self.client = client
        self.re_cache_playlists = re_cache_playlists
        self.playlists = []
        self.cache = cache
        self.__get_global_playlists(countries)

    def get_random_global_songs(self, count):
        """
        Retrieve `count` songs from different playlists
        """
        playlists = self.__choose_playlists(count)
        artists = set()
        songs = []

        for playlist in playlists:
            chosen_song = None
            # Make sure that no artist in a proposed new track is listed on a track already in the list
            while not chosen_song or len(set(chosen_song.artists) - artists) < len(chosen_song.artists):
                chosen_song = self.__one_song_from_playlist(playlist.id)

            songs.append(chosen_song)     
            artists.update(chosen_song.artists)           

        return songs

# ---------------- ---------------- ---------------------#
# ----------------     private      ---------------------#
# ---------------- ---------------- ---------------------#

    def __get_global_playlists(self, countries):
        if len(self.playlists) > 0:
            return self.playlists

        cached_playlists = []
        if not self.re_cache_playlists:
            cached_playlists = self.cache.load_playlists()

        # Fetch from cache
        if len(cached_playlists) == 0:
            print("No cached regional playlists found. Fetching a new list.")
            self.playlists = list(filter(None, [self.__get_spotify_playlist_for_country(id, countries[id]) for id in countries.keys()]))
            self.cache.save_playlists(self.playlists)
        else:
            print("Found a regional playlist cache. Loading.")
            self.playlists = self.cache.load_playlists()
            cached_country_ids = set([playlist.country_id for playlist in self.playlists])
            requested_country_ids = set([id for id in countries.keys()])
            missing_country_ids = requested_country_ids - cached_country_ids

            if (len(missing_country_ids) > 0 and self.re_cache_playlists):
                print(f"{len(missing_country_ids)} countries were missing from the regional playlist cache.")
                updated_cache = False

                for country_id in missing_country_ids:
                    playlist = self.__get_spotify_playlist_for_country(country_id, countries[country_id])
                    if playlist:
                        self.playlists.append(playlist)
                        updated_cache = True

                if updated_cache:
                    self.cache.save_playlists(self.playlists)
            
        return self.playlists

    def __one_song_from_playlist(self, playlist_id):
        tracks = self.client.get_playlist_tracks(playlist_id)
        if (len(tracks) < 1):
            print(f"Playlist {playlist_id} has no tracks")
            return None
        return tracks[random.randint(0, len(tracks) - 1)]

    def __choose_playlists(self, count):
        if (count > len(self.playlists)):
            return self.playlists

        candidates = self.playlists.copy()
        chosen = []

        for i in range(0, count):
            chosen.append(candidates.pop(random.randint(0, len(candidates) - 1)))
        
        return chosen
        
    def __get_spotify_playlist_for_country(self, country_id, country_name):
        """
        Not all countries have their own Spotify-managed "Top 50" playlist, so we best effort search for those that do. 
        https://community.spotify.com/t5/Closed-Ideas/Playlists-quot-Top-50-quot-and-quot-Top-viral-quot-Albanian/idi-p/5328706

        :param country_id: ISO 3166 country code
        """
        search_terms = ['Top 50', 'Viral 50', 'Hot']
        print(f"Searching in {country_name}")
        for term in search_terms:
            playlists = self.client.search_playlists(f"{term} {country_name}", country_id, True)

            filtered_playlists = [Playlist(playlist['id'], playlist['name'], playlist['owner']['display_name'], country_id) for playlist in playlists if self.__meets_playlist_requirements(playlist)]
            
            if (len(filtered_playlists) > 0):
                print(f"Found playlist for {country_name}: {filtered_playlists[0].name}")
                return filtered_playlists[0]
        return None

    def __meets_playlist_requirements(self, playlist_json):
        return playlist_json['owner']['display_name'] == 'Spotify'
