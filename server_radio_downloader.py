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
        """
        try:
            auth_id = spotipy.oauth2.SpotifyOAuth(
                client_id=credentials.client_id,
                client_secret=credentials.client_secret,
                redirect_uri='http://localhost/',
                state=None,
                # scope='playlist-read-private playlist-modify-private playlist-modify-public user-read-private user-library-read',
                scope='playlist-read-private playlist-modify-private playlist-modify-public user-library-read user-read-private',
                username=credentials.username)

            token = auth_id.refresh_access_token(credentials.refresh_token)\
            ['access_token']

            return spotipy.Spotify(auth=token)

        except Exception:
            print('Invalid credentials. Exiting now...')
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

        tracks = {0:{'artist': '', 'song': ''}}
        counter = 1

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

                # Check if a new song is on.
                # If not go through the while loop again.
                if artist == tracks[counter-1]['artist'] and \
                song == tracks[counter-1]['song']:
                    continue

                # Need to discard all 'songs' that start with
                # 'Cinema' or 'Television' since these are jingles and not
                # actual songs
                if artist in ('Cinema', 'Television'):
                    continue

                # If we have a new song, put that into the dictionary
                tracks.update({counter:{'artist': artist, 'song': song}})
                counter += 1

                print(counter)

                # Let's process the last 10 songs and add them to the playlist
                if counter % 2 == 0:
                    # First get the spotify ID of each song in the batch
                    updated_json_dict = self.get_spotify_track_ids(tracks)
                    # Now add all the songs to our playlist named 'Djam Radio'
                    self.populate_playlist(updated_json_dict)

                    # Let's save to disk the songs that we've scraped
                    with open(output_filename, 'a') as file:
                        for song_num in tracks:
                            file.write(tracks[song_num]['artist'] + '///' +\
                                       tracks[song_num]['song'] + '\n')

    # Now we can clear the tracks in memory but keep the latest
    # song scraped in the dic so we don't get a duplicate on the next iteration
    # of the while loop
                    temp_tracks = {1:{'artist': tracks[counter-1]['artist'],
                                      'song': tracks[counter-1]['song']}}
                    print(temp_tracks)
                    tracks = temp_tracks
                    counter = 2

    # Let's also restart the browser, so that we don't get timeouts
                    browser.quit()
                    browser = self.new_browser_instance()

            # If we hit an exception, let's save to file what we have in memory
            # so that we don't lose that data
            except Exception as ex:
                print('Caught an exception', ex)
                with open(output_filename, 'a') as file:
                    for song_num in tracks:
                        file.write(tracks[song_num]['artist'] + '///' +\
                                   tracks[song_num]['song'] + '\n')

                # Might have had an issue with selenium, so restart the browser
                browser.quit()
                browser = self.new_browser_instance()

    def get_spotify_track_ids(self, json_dict):
        """
        Searches the spotify database for a track ID based on the name of the
        artist and name of the song, as specified in the json dict.
        Not all songs posted on the webradio appear exactly as is when
        searching spotify (e.g. because of a typo in the web radio info).
        If searching artist + song name doesn't match with a spotify song, try
        to modify the search string to match.
        Updates the json dict to include the new field, track_id.
        This track_id is required to populate the spotify playlist.
        """

        spotify = self.identify()

        for song_num in json_dict:
            search_string = json_dict[song_num]['artist'] + ' ' + \
            json_dict[song_num]['song']

            try:
                results = spotify.search(q=search_string, limit=1, type='track')
                temp_id = results['tracks']['items'][0]['id']
                json_dict[song_num].update({'spotify_id':temp_id})
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
                    json_dict[song_num]['artist'].split('(')[0].strip() \
                    + ' ' + json_dict[song_num]['song'].split('(')[0].strip()

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']
                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with song ", search_string)
                    continue

            # If that doesn't work, reset search_string
            except IndexError:
                search_string = json_dict[song_num]['artist'] + ' ' + \
                json_dict[song_num]['song']

            # If that doesn't work, see if there's a 'feat' in the song or
            # artist name that we can remove, and only keep what comes before
            # the 'feat'.

            try:
                if 'feat' in search_string:
                    search_string = json_dict[song_num]['artist'].split('feat')[0].strip() \
                    + ' ' + json_dict[song_num]['song'].split('feat')[0].strip()

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']
                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with song ", search_string)
                    continue

            except IndexError:
                pass

            # If that fails, next thing to try is to see if the song can be
            # found with only the first word of the song + full name of artist

            try:
                if len(json_dict[song_num]['song']) > 1:
                    search_string = json_dict[song_num]['artist'] + ' ' + \
                    json_dict[song_num]['song'].split()[0]

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']

                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with overly long song ",
                          search_string)
                    continue

            except IndexError:
                pass

            # If that fails, next thing to try is to see if the song can be
            # found with only the two first word of the artist + full name of
            # song
            try:
                if len(json_dict[song_num]['artist']) > 2:
                    search_string = ''.join(json_dict[song_num]['artist'].split()[:2]) + \
                     ' ' + json_dict[song_num]['song']

                    results = spotify.search(q=search_string,
                                          limit=1,
                                          type='track')

                    temp_id = results['tracks']['items'][0]['id']

                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with overly long artist name ",
                          search_string)

            except IndexError:
                pass

            # If nothing is found at that point, then fuck it, move on

        return json_dict

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

    def populate_playlist(self, json_dict):
        """
        Given a json_dict of songs that have been scraped, this function
        will add the songs of the json to the playlist whose name
        was specified in the credentials file, if they
        aren't already in there (i.e. checks for duplicates).

        Need to pass in a json dict which contains the songs that you want to
        add, as created by RadioDownloader().djam_radio().

        The playlist_id was determined upon instantiation of this class.
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

        # Now let's extract all the song ids from the dictionary that was
        # passed in. In the process, let's check that the songs that we want to
        # add don't exist in the playlist already.
        # If there are any songs for which we didn't find a spotify ID,
        # let's store those in reject_songs o we can write them to disk later.
        list_song_ids = []
        reject_songs = []
        for song in json_dict.values():
            try:
                if song['spotify_id'] not in existing_songs:
                    list_song_ids.append(song['spotify_id'])
            except KeyError:
                reject_songs.append([song['artist'], song['song']])

        # Now that we've compiled all of the new songs into one list,
        # let's add them to the playlist!
        if list_song_ids:
            spotify.user_playlist_add_tracks(credentials.username,
                                             playlist_id=self.playlist_id,
                                             tracks=list_song_ids)

            print('Playlist populated...')

        # If any, let's write the name of songs which we couldn't add to the
        # playlist to file
        if reject_songs:
            with open('reject_songs.txt', 'a') as file:
                for song in reject_songs:
                    if song != ['', '']:
                        file.write(str(song))


USER = RadioDownloader()
USER.djam_radio('list_of_songs.txt')
