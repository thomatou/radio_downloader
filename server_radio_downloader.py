import traceback
import sys
import time
from datetime import datetime
import schedule
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
                print('Current time is: ',
                     datetime.utcnow().strftime("%c"))
                time.sleep(30)

        print('Invalid credentials on 3 separate attempts. Exiting program...')
        print(datetime.utcnow().strftime("%c"))
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
        global tracks
        # These are the paths to the info we're interested in on the webpage
        artist_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[1]/a'
        song_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[2]'

        try:
            browser = self.new_browser_instance()
            browser.get('https://www.djamradio.com/')

            artist = browser.find_element_by_xpath(artist_path).text
            song = browser.find_element_by_xpath(song_path).text

            temp_track = (artist,song)

            # Need to discard all 'songs' that start with
            # 'Cinema' or 'Television' since these are jingles and not
            # actual songs
            # In that case, return from this function, which the scheduler
            # will call again in one minute.
            if artist in ('Cinema', 'Television'):
                browser.quit()
                return

            # Add the temp song to the tracks. Since tracks is a set, if
            # temp_track has already been added to the set, it won't get
            # added again
            tracks.add(temp_track)
            print(len(tracks))

            # Let's process the last 10 songs and add them to the playlist
            if len(tracks) % 3 == 0:
                # First get the spotify ID of each song in the batch
                updated_tracks = self.get_spotify_track_ids(tracks)
                # Now add all the songs to our playlist named 'Djam Radio'
                self.populate_playlist(updated_tracks)
                print(datetime.utcnow().strftime("%c"))

                # Let's save to disk the songs that we've scraped

                # How do you prevent the last song from getting
                # written to file twice?
                with open(output_filename, 'a') as file:
                    for song in tracks:
                        file.write(song[0] + '///' + song[1] + '\n')

                # Now we can clear the tracks in memory
                tracks = set()

        # Let's also exit the browser before we leave
            browser.quit()

            # Let's return tracks so that the scheduler can keep track of it
            # and use it in the next iteration
            return tracks

        # If we hit an exception, let's save to file what we have in memory
        # so that we don't lose that data
        except Exception as ex:
            print('Caught an exception', ex)
            traceback.print_tb(ex.__traceback__)
            print(datetime.utcnow().strftime("%c"))
            with open(output_filename, 'a') as file:
                for song in tracks:
                    file.write(song[0] + '///' + song[1] + '\n')

            # Might have had an issue with selenium, so restart the browser
            browser.quit()

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
        If such a playlist is not found, one with that exact name will be
        created, and its id returned.
        """
        spotify = self.identify()
        counter = 0
        current_playlist_ids = [(None,None)]

        # Have to iterate through all the playlists of the user
        while current_playlist_ids:
            current_playlists = spotify.user_playlists(
                user=credentials.username,
                limit=50,
                offset=counter)

            current_playlist_ids = [(item['name'],item['id']) for
                                    item in current_playlists['items']]

            for name, id in current_playlist_ids:
                if name == name_of_playlist:
                    return id

            counter += len(current_playlist_ids)
            # print(counter)
            # print(current_playlist_ids)

        # If we can't find the playlist with the name specified, create it!
        print("A playlist with name:", name_of_playlist, 'was not found.')

        return self.create_spotify_playlist(name_of_playlist)

    def create_spotify_playlist(self, name_of_playlist):
        """
        Creates a new playlist with the desired name, and returns the id of
        the playlist.

        Only used in the event that the user specifies a playlist name that
        doesn't exist in their list of playlists.
        """

        try:
            spotify = self.identify()
            new_playlist = spotify.user_playlist_create(credentials.username, name=name_of_playlist)
            print('Created playlist with name:', name_of_playlist)
            return new_playlist['id']

        except Exception as ex:
            print('Failed to create playlist with name', playlist_name)
            print('Exception:', ex)

    def check_playlist_name(self):
        """
        Checks if the current playlist name matches what it should be.
        If not, amends the name of the playlist name to what it should be.
        Assuming that this function is called every day, the playlist name
        change happens on the first day of every month.
        """

        current_playlist_name = 'Djam Radio ' + \
                datetime.utcnow().strftime("%B") + ' ' + \
                datetime.utcnow().strftime('%Y')

        # this only amends playlist_id if current_playlist_name doesn't exist
        # in the user's list of playlists, i.e. if we're in a new month of the
        # year

        self.playlist_id = self.get_spotify_playlist_id(current_playlist_name)

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


if __name__ == '__main__':

    USER = RadioDownloader()
    tracks = set()

    schedule.every().minute.do(USER.djam_radio, 'list_of_songs.txt')

    while True:
        schedule.run_pending()
        time.sleep(1)
