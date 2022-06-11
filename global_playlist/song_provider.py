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
        playlist_ordering = self.__random_playlist_ordering()

        artists = set()
        songs = []

        # If the number of artists in the song's list is decreased when we remove all already chosen artists, 
        # we can drop the song because we don't want artists showing up multiple times
        artist_not_present = lambda s: len(set(s.artist_ids) - artists) == len(s.artist_ids)

        used_songs = self.cache.load_used_songs()

        rejection_set = set(used_songs)

        song_not_rejected = lambda song: song.id not in rejection_set

        while (len(songs) < count and len(playlist_ordering) > 0):
            # The ordering is random, so it doesn't really matter if we take from the front or back
            next_playlist = playlist_ordering.pop()

            valid_songs = self.__valid_songs_from_playlist(next_playlist.id, [artist_not_present, song_not_rejected])

            if (len(valid_songs) == 0):
                continue
            
            chosen_song = valid_songs[random.randint(0, len(valid_songs) - 1)]

            songs.append(chosen_song)     
            artists.update(chosen_song.artist_ids)           

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

    def __valid_songs_from_playlist(self, playlist_id, predicates = []):
        songs = self.client.get_playlist_tracks(playlist_id)

        # This beauty applies all the predicates
        return list(filter(lambda song: all([predicate(song) for predicate in predicates]), songs))


    def __random_playlist_ordering(self):
        candidates = self.playlists.copy()
        chosen = []

        for i in range(0, len(self.playlists)):
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
