
class PlaylistManager:
    GLOBAL_PLAYLIST_NAME = "A beta trip around the world"

    def __init__(self, client):
        self.client = client

    def create_global_playlist(self, songs):
        """
        Create the global playlist if it doesn't exist and populate it with a new set of songs.
        """
        playlist_id = self.__get_existing_global_playlist_id()

        if not playlist_id:
            print("Creating new global playlist")
            playlist_id = self.__create_global_playlist()
        else:
            print("Cleaning up existing global playlist")
            self.__clear_out_global_playlist(playlist_id)

        print("Populating global playlist")
        self.__add_songs_to_global_playlist(playlist_id, songs)

# ---------------- ---------------- ---------------------#
# ----------------     private      ---------------------#
# ---------------- ---------------- ---------------------#   

    def __get_existing_global_playlist_id(self):
        current_user_playlists = self.client.get_current_user_playlists()

        filtered_playlists = list(filter(lambda playlist: playlist['name'] == self.GLOBAL_PLAYLIST_NAME, current_user_playlists))

        if (len(filtered_playlists) == 1):
            return filtered_playlists[0]['id']

        if (len(filtered_playlists) == 0):
            return None

        raise Exception("Multiple playlists matched the global playlist search")

    def __create_global_playlist(self):
        return self.client.create_playlist_for_current_user(
            self.GLOBAL_PLAYLIST_NAME,
            "An automatically generated playlist with songs selected from random \"Top 50\" playlists around the world! 🌎"
        )

    def __clear_out_global_playlist(self, playlist_id):
        tracks = self.client.get_playlist_tracks(playlist_id)
        self.client.remove_items_from_playlist(playlist_id, tracks)

    def __add_songs_to_global_playlist(self, playlist_id, songs):
        self.client.add_items_to_playlist(playlist_id, songs)
