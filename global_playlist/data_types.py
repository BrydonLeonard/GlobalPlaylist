class Playlist:
    def __init__(self, id, name, owner, country_id):
        self.id = id
        self.name = name
        self.owner = owner
        self.country_id = country_id
    
    def __str__(self):
        return f"[{self.id}] '{self.name}' by '{self.owner}' ({self.country_id})"

    def __repr__(self):
        return self.__str__()

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            'country_id': self.country_id
        }

class Song:
    def __init__(self, id, name, uri, artist_ids, artist_names):
        self.id = id
        self.name = name
        self.uri = uri
        # Not super great to store these like this, since there's nothing linking IDs to names,
        # but for now I only use the names when I want some human-readable version of a given
        # song's artists, so this is fine.
        self.artist_ids = artist_ids
        self.artist_names = artist_names

    def __str__(self):
        return f"[{self.id}] {self.name} ({','.join(self.artist_names)})"

class ClientToken:
    def __init__(self, token, refresh_token, expires_at):
        self.token = token
        self.refresh_token = refresh_token
        self.expires_at = expires_at

class ConfigKeys:
    APP_SECRET = "app_secret"
    APP_ID = "app_id"