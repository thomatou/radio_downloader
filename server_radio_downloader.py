import traceback
import sys
import time
import spotipy
from selenium.webdriver.firefox.options import Options
from selenium import webdriver
import credentials


class RadioDownloader:
    """
    Enables scraping music from www.djamradio.com and dumping all the songs
    into a Spotify playlist.
    """
    def __init__(self):
        """
        Verifies that the credentials of the user (client ID, client secret,
        username and refresh token) are accepted by the Spotify API before
        proceeding to any scraping.
        Checks that the user has a playlist that matches with the name
        specified.
        """
        self.identify()
        self.playlist_id = \
        self.get_spotify_playlist_id(credentials.playlist_name)

    def identify(self):
        """
        Identify with the spotify API. Will automatically refresh the access
        token to enable the user to read and modify spotify playlists.
        If the program fails to identify on the first attempt, it will try
        identifying a couple more times before exiting.
        """
        counter = 0
        while counter < 3:
            try:
                auth_id = spotipy.oauth2.SpotifyOAuth(
                    client_id=credentials.client_id,
                    client_secret=credentials.client_secret,
                    redirect_uri='http://localhost/',
                    state=None,
                    scope='playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-read-private',
                    username=credentials.username)

                token = auth_id.refresh_access_token(credentials.refresh_token)\
                ['access_token']

                return spotipy.Spotify(auth=token)

            except Exception:
                counter += 1
                print('Invalid credentials. Retrying...')
                print('Current time is: ', time.)
                time.sleep(30)

        print('Invalid credentials on 3 separate attempts. Exiting program...')
        print(time.strftime('%c'))
        sys.exit()


    def new_browser_instance(self):
        """Creates a headless Selenium browser instance."""

        options = Options()
        options.headless = True

        return webdriver.Firefox(options=options,
                    executable_path=credentials.geckodriver_executable_path)

    def djam_radio(self, output_filename):
        """
        Scrapes data from the djam radio website every 60 seconds.
        Checks if the scraped data is different from what was last scraped.
        If so, the data is saved in memory.
        Every 10 new songs, those will be dumped into the spotify playlist,
        the names of the songs will be written to file, and the dictionary
        containing the songs will be cleared out.
        Will only stop with keyboard interrupt.
        The songs are also saved as text in the file output_filename.
        """

        tracks = set()

        # These are the paths to the info we're interested in on the webpage
        artist_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[1]/a'
        song_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[2]'

        browser = self.new_browser_instance()

        while True:
            try:
                browser.get('https://www.djamradio.com/')
                # Sleep 60 seconds since songs tend to be > 1 minute in length
                time.sleep(60)

                artist = browser.find_element_by_xpath(artist_path).text
                song = browser.find_element_by_xpath(song_path).text

                temp_track = (artist,song)

                # Need to discard all 'songs' that start with
                # 'Cinema' or 'Television' since these are jingles and not
                # actual songs
                if artist in ('Cinema', 'Television'):
                    continue

                # Check if a new song is on.
                # If not go through the while loop again.
                if temp_track in tracks:
                    continue

                # If we have a new song, put that into the dictionary
                tracks.add(temp_track)
                print(len(tracks))

                # Let's process the last 10 songs and add them to the playlist
                if len(tracks) % 10 == 0:
                    # First get the spotify ID of each song in the batch
                    updated_tracks = self.get_spotify_track_ids(tracks)
                    # Now add all the songs to our playlist named 'Djam Radio'
                    self.populate_playlist(updated_tracks)
                    print(time.strftime('%c'))

                    # Let's save to disk the songs that we've scraped

            # How do you prevent the last song from getting
            # written to file twice?
                    with open(output_filename, 'a') as file:
                        for song in tracks:
                            file.write(song[0] + '///' + song[1] + '\n')

                    # Now we can clear the tracks in memory
                    tracks = set()

    # Let's also restart the browser, so that we don't get timeouts
                    browser.quit()
                    browser = self.new_browser_instance()

            # If we hit an exception, let's save to file what we have in memory
            # so that we don't lose that data
            except Exception as ex:
                print('Caught an exception', ex)
                traceback.print_tb(ex.__traceback__)
                print(time.strftime('%c'))
                with open(output_filename, 'a') as file:
                    for song in tracks:
                        file.write(song[0] + '///' + song[1] + '\n')

                # Might have had an issue with selenium, so restart the browser
                browser.quit()
                browser = self.new_browser_instance()

    def get_spotify_track_ids(self, song_set):
        """
        Searches the spotify database for a track ID based on the name of the
        artist and name of the song, as specified in the set passed in.
        Each element of the set is a list containing the artist in first
        position, and song name in second position.
        Not all songs posted on the webradio appear exactly as is when
        searching spotify (e.g. because of a typo in the web radio info).
        If searching artist + song name doesn't match with a spotify song, try
        to modify the search string to match.
        Returns a list of all the track_ids that were.
        This track_id is required to populate the spotify playlist.
        """

        spotify = self.identify()
        track_ids = []
        reject_songs = []

        for artist, song in song_set:
            search_string = artist + ' ' + song

            try:
                results = spotify.search(q=search_string, limit=1, type='track')
                temp_id = results['tracks']['items'][0]['id']
                track_ids.append(temp_id)
                continue

            except IndexError:
                pass

            # If there's an issue with the search, that's possibly because
            # the song or artist is misspelt. Easiest thing to do is remove
            # the brackets if there are any in the song name (usually a
            # '(feat. artist x)', which trips up the spotify search)
            # Let's remove those

            try:
                if '(' in search_string:
                    search_string = \
                    artist.split('(')[0].strip() \
                    + ' ' + song.split('(')[0].strip()

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']
                    track_ids.append(temp_id)
                    print("IndexError caught with brackets in song ",
                    artist, ' ', song)
                    continue

            # If that doesn't work, reset search_string
            except IndexError:
                search_string = artist + ' ' + song

            # If that doesn't work, see if there's a 'feat' in the song or
            # artist name that we can remove, and only keep what comes before
            # the 'feat'.

            try:
                if 'feat' in search_string:
                    search_string = artist.split('feat')[0].strip() \
                    + ' ' + song.split('feat')[0].strip()

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']
                    track_ids.append(temp_id)
                    print("IndexError caught with song ", search_string)
                    continue

            except IndexError:
                pass

            # If that fails, next thing to try is to see if the song can be
            # found with only the first word of the song + full name of artist

            try:
                if len(song.split()) > 1:
                    search_string = artist + ' ' + \
                    song.split()[0]

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']
                    track_ids.append(temp_id)
                    print("IndexError caught with overly long song ",
                          search_string)
                    continue

            except IndexError:
                pass

            # If that fails, next thing to try is to see if the song can be found with only the two first word
            # of the artist + full name of song
            try:
                if len(artist.split()) > 2:
                    search_string = \
                    ' '.join(artist.split()[:2]) + \
                     ' ' + song

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']

                    track_ids.append(temp_id)
                    print("IndexError caught with overly long artist name ",
                          search_string)

            except IndexError:
            # If nothing is found at that point, then make a note of this
            # and move on
                reject_songs.append(artist + '///' + song)
                pass


        # Write the songs that weren't found on spotify to file
        with open('reject_songs.txt', 'a') as file:
            for song in reject_songs:
                file.write(song + '\n')

        # And return the list of the spotify ids of the songs that
        # can be added to the playlist
        return track_ids

    def get_spotify_playlist_id(self, name_of_playlist):
        """
        Will look into a user's playlists and return the id of a playlist
        whose name matches exactly the name specified. Case-sensitive.
        """
        spotify = self.identify()

        playlists = spotify.user_playlists(credentials.username, limit=50)

        while True:

            for item in playlists['items']:
                if item['name'] == name_of_playlist:
                    return item['id']

            print('Playlist not found. Input is case-sensitive.')
            print('Please re-enter the name of the playlist whose ID you wish\
                   to access:')

            name_of_playlist = input()

    def populate_playlist(self, song_ids):
        """
        Given a list of spotify songs IDs, this function will add these songs
        to the playlist whose name was specified in the credentials file, if
        they aren't already in there (i.e. checks for duplicates).

        Need to pass in a list of spotify song IDs, as outputted by
        self.get_spotify_track_ids().

        The playlist_id is determined upon instantiation of this class.
        """

        # First, let's access the playlist of interest
        spotify = self.identify()

        # And let's store in a set all the spotify IDs of the songs that
        # already are in the playlist (to avoid introducing duplicates)
        counter = 0
        existing_songs = set()
        current_song_ids = [0]

        while current_song_ids:
            current_playlist_songs = spotify.user_playlist_tracks(
                user=credentials.username,
                playlist_id=self.playlist_id,
                offset=counter)

            current_song_ids = [item['track']['id'] for item in \
                                current_playlist_songs['items']]

            counter += len(current_song_ids)

            existing_songs.update(current_song_ids)

        # Let's check that the songs that we want to add don't exist in the
        # playlist already.

        list_song_ids = []
        for song in song_ids:
            if song not in existing_songs:
                list_song_ids.append(song)

        # Now that we've compiled all of the new songs into one list,
        # let's add them to the playlist!
        if list_song_ids:
            spotify.user_playlist_add_tracks(credentials.username,
                                             playlist_id=self.playlist_id,
                                             tracks=list_song_ids)
            print('Playlist populated...')
        else:
            print('No new songs to add...')



USER = RadioDownloader()

print(USER.get_spotify_playlist_id('Djam Radio'))
#USER.djam_radio('list_of_songs.txt')
#
#
# with open('list_of_songs.txt', 'r') as f:
#     data = f.read().split('\n')
#
# list_songs = []
# for song in data:
#     if '///' in song and len(song) > 3:
#         artist, track = song.split('///')[0], song.split('///')[1]
#         list_songs.append([artist,track])
#
#
# USER = RadioDownloader()
# song_ids = USER.get_spotify_track_ids(list_songs)
#
# USER.populate_playlist(song_ids)
