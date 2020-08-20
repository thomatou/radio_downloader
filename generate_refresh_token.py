import spotipy
import credentials


id = spotipy.oauth2.SpotifyOAuth(
                    client_id=credentials.client_id,
                    client_secret=credentials.client_secret, redirect_uri='http://localhost/',
                    state=None,
                    scope='playlist-read-private playlist-modify-private',
                    username=credentials.username)

token_info = id.get_access_token()

print(token['refresh_token'])
