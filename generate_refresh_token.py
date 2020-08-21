import spotipy
import credentials

SPOTIFY = spotipy.oauth2.SpotifyOAuth(
    client_id=credentials.client_id,
    client_secret=credentials.client_secret,
    redirect_uri='http://localhost/',
    state=None,
    scope='playlist-read-private playlist-modify-private',
    username=credentials.username)

TOKENS = SPOTIFY.get_cached_token()

print("This is your refresh token: ", TOKENS['refresh_token'])
