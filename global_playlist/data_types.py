class Playlist:
    def __init__(self, id, name, owner, country_id):
        self.id = id
        self.name = name
        self.owner = owner
        self.country_id = country_id
    
    def __str__(self):
        return f"[{self.id}] {self.name} (owner:{self.owner})"

    def dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'owner': self.owner,
            'country_id': self.country_id
        }

class Song:
    def __init__(self, id, name, uri, artists):
        self.id = id
        self.name = name.encode('utf-8')
        self.uri = uri
        self.artists = artists

    def __str__(self):
        return f"[{self.id}] {self.name} ({self.artist})"

class ClientToken:
    def __init__(self, token, refresh_token, expires_at):
        self.token = token
        self.refresh_token = refresh_token
        self.expires_at = expires_at