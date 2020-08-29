import spotipy
import credentials

SPOTIFY = spotipy.oauth2.SpotifyOAuth(
    client_id=credentials.client_id,
    client_secret=credentials.client_secret,
    redirect_uri='http://localhost/',
    state=None,
    scope='playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-read-private',
    username=credentials.username)

ACCESS_TOKENS = SPOTIFY.get_access_token(as_dict=False)
CACHED_TOKENS = SPOTIFY.get_cached_token()
print("This is your refresh token: ", CACHED_TOKENS['refresh_token'])
