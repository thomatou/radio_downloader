from selenium import webdriver
import json
import time
import spotipy
import spotipy.util as util
import credentials
import sys
from selenium.webdriver.firefox.options import Options


class RadioDownloader:
    def __init__(self):
        """
        Will probably want to instantiate with the spotify username
        + API key in order to create a new playlist
        """
        self.spotify_username = credentials.username
        # Mock identify here, just to check before the program gets going
        # that we're not going to have authorisation issues later.
        self.identify()

    def identify(self):
        """
        Identify with the spotify API. Will automatically refresh the access
        token to enable the user to read and modify spotify playlists.
        """
        try:
            id =  spotipy.oauth2.SpotifyOAuth(
                                client_id=credentials.client_id,
                                client_secret=credentials.client_secret, redirect_uri='http://localhost/',
                                state=None,
                                scope='playlist-read-private playlist-modify-private',
                                username=self.spotify_username)

            token = id.refresh_access_token(credentials.refresh_token)\
            ['access_token']

            return spotipy.Spotify(auth=token)

        except Exception:
            print('Invalid credentials. Exiting now...')
            sys.exit()

    def djam_radio(self, output_filename):
        """
        Scrapes data from the djam radio website every 60 seconds.
        Checks if the scraped data is different from what was last scraped.
        If so, data is saved.
        Currently, this will only stop with keyboard interrupt, at which point
        the dict is returned as well as written to file whose name has to be
        passed in as an argument.
        """
        options = Options()
        options.headless = True

        tracks = {0:{'artist': '', 'song': ''}}

        counter = 1
        artist_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[1]/a'
        song_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[2]'

        browser = webdriver.Firefox(
                            options=options,
                            executable_path='/usr/bin/geckodriver')

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
                if artist == 'Cinema' or artist == 'Television':
                    continue

                # If we have a new song, put that into the dictionary
                tracks.update({counter:{'artist': artist, 'song': song}})
                counter += 1
                print(counter)

                if counter % 10 == 0:
                    # Let's process the last 10 songs and add them to the playlist
                    updated_json_dict = self.get_spotify_track_ids(tracks)

                    self.populate_playlist('Djam Radio', updated_json_dict)

                    # Let's save to disk the songs that we've scraped
                    with open(output_filename, 'a') as file:
                        for song_num in tracks:
                            file.write(tracks[song_num]['artist'] + '///' +\
                                       tracks[song_num]['song'] + '\n')

    # Now we can overwrite the name of the tracks in memory but keep the latest
    # song scraped in the dic so we don't get a duplicate on the next iteration
    # of the  while loop
                    temp = {1:{'artist': tracks[counter-1]['artist'], 'song': tracks[counter-1]['song']}}
                    print(temp)
                    tracks = temp
                    counter = 2

    # Let's also restart the browser, so that we don't get timeouts
                    browser.quit()
                    browser = webdriver.Firefox(
                                    options=options,
                                    executable_path='/usr/bin/geckodriver')

            except Exception as e:
                print('Caught an exception', e)
                with open(output_filename, 'a') as file:
                    for song_num in tracks:
                        file.write(tracks[song_num]['artist'] + '///' +\
                                   tracks[song_num]['song'] + '\n')
                browser.quit()
                browser = webdriver.Firefox(
                                options=options,
                                executable_path='/usr/bin/geckodriver')
                continue

    def get_spotify_track_ids(self, json_dict):
        """
        Searches the spotify database for a track ID based on the name of the
        artist and name of the song, as specified in the json dict.
        Updates the json dict to include the new field, track_id.
        This track_id is then used to populate the spotify playlist
        """

        sp = self.identify()

        for song_num in json_dict:
            search_string = json_dict[song_num]['artist'] + ' ' + json_dict[song_num]['song']

            try:
                temp = sp.search(q=search_string, limit=1, type='track')
                temp_id = temp['tracks']['items'][0]['id']
                json_dict[song_num].update({'spotify_id':temp_id})
                continue
            except IndexError:
                pass

            s = search_string
            # If there's an issue with the search, that's possibly because
            # the song or artist is misspelt. Easiest thing to do is remove
            # the brackets if there are any in the song name (usually a
            # '(feat. artist x)', which trips up the spotify search)
            # Let's remove those
            try:
                if s.find('(') < s.find(')'):
                    s = s[:s.find('(')].strip()
                    temp = sp.search(q=s,
                                     limit=1,
                                     type='track')

                    temp_id = temp['tracks']['items'][0]['id']
                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with song ", s)
                    continue
            except IndexError:
                pass

            # If that doesn't work, see if there's a 'feat' in the song or
            # artist name that we can remove, and only keep what comes before
            # the 'feat'.
            try:
                if 'feat' in s:
                    s = json_dict[song_num]['artist'].split('feat')[0] +\
                        json_dict[song_num]['song'].split('feat')[0]

                    temp = sp.search(q=s,
                                     limit=1,
                                     type='track')

                    temp_id = temp['tracks']['items'][0]['id']
                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with song ", s)
                    continue

            except IndexError:
                pass
            # If that fails, next thing to try is to see if the song can be
            # found with only the first word of the song + full name of artist

            try:
                if len(json_dict[song_num]['song']) > 1:
                    search_string = json_dict[song_num]['artist'] + ' ' + json_dict[song_num]['song'].split()[0]
                    temp = sp.search(q=search_string,
                                     limit=1,
                                     type='track')
                    temp_id = temp['tracks']['items'][0]['id']

                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with overly long song ", s)
                    continue
            except IndexError:
                pass

            # If that fails, next thing to try is to see if the song can be
            # found with only the two first word of the artist + full name of
            # song
            try:
                if len(json_dict[song_num]['artist']) > 2:
                    search_string = ' '.join(json_dict[song_num]['artist'].split()[:2]) + ' ' + json_dict[song_num]['song']
                    temp = sp.search(q=search_string,
                                     limit=1,
                                     type='track')
                    temp_id = temp['tracks']['items'][0]['id']

                    json_dict[song_num].update({'spotify_id':temp_id})
                    print("IndexError caught with overly long artist name ", s)

            except IndexError:
                pass

            # If nothing is found at that point, then fuck it, move on

        return json_dict

    def get_spotify_playlist_id(self, name_of_playlist):
        """
        Will look into a user's playlists and return the id of a playlist
        whose name matches exactly the name specified. Case-sensitive.
        """
        sp = self.identify()

        playlists = sp.user_playlists('thomatou', limit=50)

        while True:

            for item in playlists['items']:
                if item['name'] == name_of_playlist:
                    return item['id']

            print('Playlist not found. Input is case-sensitive.')
            print('Please re-enter the name of the playlist whose ID you wish\
                   to access:')

            name_of_playlist = input()

    def populate_playlist(self, playlist_name, json_dict):
        """
        Given a playlist_id and a json_dict of songs to add to the playlist,
        this function will add the songs of the json to the playlist, if they
        aren't already in them (i.e. automatically checks for duplicates).

        The playlist_id can be returned by self.create_spotify_playlist() if
        you wish to create a new playlist or by self.get_spotify_playlist_id()
        if you already have a playlist to which you want to add songs.

        Need to pass in a json dict which contains the songs that you want to
        add, as created by RadioDownloader().djam_radio().
        """

        sp = self.identify()

        # First, let's access the playlist of interest
        playlist_id = self.get_spotify_playlist_id(playlist_name)

        # And let's store in a set all the spotify IDs of the songs that
        # already are in the playlist (to avoid introducing duplicates)
        counter = 0
        existing_songs = set()

        while True:
            current_playlist_songs = sp.user_playlist_tracks(
                                    user=self.spotify_username,
                                    playlist_id=playlist_id,               offset=counter)

            current_song_ids = [item['track']['id'] for item in \
                            current_playlist_songs['items']]

            if not current_song_ids:
                break

            counter += len(current_song_ids)

            existing_songs.update(current_song_ids)

        # Now let's extract all the song ids from the dictionary that was
        # passed in. This will be useful to minimise the number of calls to the
        # API (add all songs in one API call).
        # In the process, let's check that the songs that we want to add
        # don't exist in the playlist already
        # If there are any songs for which we didn't find a spotify ID,
        # and which can't be added to the playlist, let's store these separately
        list_song_ids = []
        reject_songs = []
        for song in json_dict.values():
            try:
                if song['spotify_id'] not in existing_songs:
                    list_song_ids.append(song['spotify_id'])
            except KeyError:
                reject_songs.append([song['artist'], song['song']])
                continue


        # Now that we've compiled all of the new songs into one list,
        # let's add them to the playlist!
        if list_song_ids:
            sp.user_playlist_add_tracks(self.spotify_username,
                                        playlist_id=playlist_id,
                                        tracks=list_song_ids)

            # Should be done!

            print('Playlist populated...')

        if reject_songs:
            with open('reject_songs.txt', 'a') as file:
                for element in reject_songs:
                    if element != ['', '']:
                        file.write(str(element))


user = RadioDownloader()
user.djam_radio('list_of_songs.txt')
