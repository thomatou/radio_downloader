from selenium import webdriver
import json
import time
import spotipy
import spotipy.util as util
import credentials
import sys

class RadioDownloader:
    def __init__(self, username):
        """
        Will probably want to instantiate with the spotify username
        + API key in order to create a new playlist
        """
        self.spotify_username = username
        # Mock identify here, just to check before the program gets going
        # that we're not going to have authorisation issues later.
        self.identify('playlist-modify-private')

    def identify(self, scope):
        """
        Identify with the spotify API. Useful scopes in this context are 'playlist-modify-private' or 'playlist-read-private'.
        """
        try:
            token = util.prompt_for_user_token(self.spotify_username,
                                           scope,
                                           credentials.client_id,
                                           credentials.client_secret,
                                           redirect_uri='http://localhost/')
        except Exception:
            print('Invalid credentials. Exiting now...')
            sys.exit()

        return spotipy.Spotify(auth=token)

    def djam_radio(self, output_filename):
        """
        Scrapes data from the djam radio website every 60 seconds.
        Checks if the scraped data is different from what was last scraped.
        If so, data is saved.
        Currently, this will only stop with keyboard interrupt, at which point
        the dict is returned as well as written to file whose name has to be
        passed in as an argument.
        """
        tracks = {0:{'artist': '', 'song': ''}}

        counter = 1
        artist_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[1]/a'
        song_path = '/html/body/div[2]/div[7]/div[1]/div[1]/div[1]/div[2]/span[2]'

        try:
            while True:
                browser.get('https://www.djamradio.com/')
                # Sleep 60 seconds since songs tend to be > 1 minute in length
                time.sleep(60)

                artist = browser.find_element_by_xpath(artist_path).text
                song = browser.find_element_by_xpath(song_path).text

                # Check if a new song is on.
                # If not go through the while loop again.
                if artist == tracks[counter-1]['artist'] and song == tracks[counter-1]['song']:
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

            # This block is only here if we want to implement a natural end
            # to the program (e.g. run through the loop for 12 hours)
            # As it is, this block doesn't get executed
            with open(output_filename, 'w') as file:
                json.dump(tracks, file, indent=2)

            browser.quit()

            return tracks

        # The program is set to only stop running when interrupted by the user,
        # at which point the dictionary is written to file in json format
        except KeyboardInterrupt:
            with open(output_filename, 'w') as file:
                json.dump(tracks, file, indent=2)

            browser.quit()
            return tracks

    def get_spotify_track_ids(self, json_dict):
        """
        Searches the spotify database for a track ID based on the name of the
        artist and name of the song, as specified in the json dict.
        Updates the json dict to include the new field, track_id.
        This track_id is then used to populate the spotify playlist
        """

        sp = self.identify(scope='playlist-modify-private')

        for song_num in json_dict:
            search_string = json_dict[song_num]['artist'] + ' ' + json_dict[song_num]['song']

            try:
                temp = sp.search(q=search_string,
                                 limit=1,
                                 type='track')
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

    def create_spotify_playlist(self,
                                playlist_name,
                                playlist_description=None):
        """
        Creates a playlist with name playlist_name.
        Returns the spotify_id of the newly created playlist.
        """

        sp = self.identify(scope='playlist-modify-private')

        playlist_data = sp.user_playlist_create(
                                            user=self.spotify_username,
                                            name=playlist_name,
                                            public=False,
                                            description=playlist_description)

        return playlist_data['id']

    def get_spotify_playlist_id(self, name_of_playlist):
        """
        Will look into a user's playlists and return the id of a playlist
        whose name matches exactly the name specified. Case-sensitive.
        """
        sp = self.identify(scope='playlist-read-private')

        playlists = sp.user_playlists('thomatou', limit=50)

        while True:

            for item in playlists['items']:
                if item['name'] == name_of_playlist:
                    return item['id']

            print('Playlist not found. Input is case-sensitive.')
            print('Please re-enter the name of the playlist whose ID you wish to access:')

            name_of_playlist = input()

    def populate_playlist(self, playlist_id, json_dict):
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

        sp = self.identify(scope='playlist-modify-private')

        # First, let's access the playlist of interest
        current_playlist = sp.user_playlist_tracks(user=self.spotify_username,
                                                   playlist_id=playlist_id)

        # And let's store in a set all the spotify IDs of the songs that
        # already are in the playlist (to avoid introducing duplicates)
        existing_songs = set(
            [item['track']['id'] for item in current_playlist['items']]
                            )

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
        sp.user_playlist_add_tracks(self.spotify_username,
                                    playlist_id=playlist_data['id'],
                                    tracks=list_song_ids)

        # Should be done!

        print('Playlist populated...')

        if reject_songs:
            print("Here is a list of the songs that weren't found on Spotify:")
            print(list_song_ids)

        print('Exiting program...')


user = RadioDownloader('thomatou')

music_list = user.djam_radio()

updated_music_list = user.get_spotify_track_ids(music_list)

djam_playlist_id = user.get_spotify_playlist_id('Djam Radio')

user.populate_playlist(djam_playlist_id, updated_music_list)
