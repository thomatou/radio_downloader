# Radio Downloader
## Get all the songs from your favourite radio station into a Spotify playlist!

This script was originally written to access the excellent music selection of [Djam Radio](www.djamradio.com). For every track played on this radio station, the name of the artist and the name of the song is posted, live, on the website.

The script scrapes this information in real-time and will run indefinitely (or until the user interrupts it). It will then add them to the Spotify playlist in batches of 10 – to minimise the number of calls to the API. Note that the script will also prevent the addition of duplicates to the playlist.

The idea here is to take advantage of [Oracle's Always Free servers](https://www.oracle.com/cloud/free/#always-free), which one can set up for, well, free, and to use it to run this script permanently, without having to keep your local machine on. You do need a credit card to set up a server, but you won't be charged for an Always Free server, which is powerful enough to run this script.

Note that this script could easily be adapted to scrape any web radio that displays the name of its songs in real time! 

Link to the Djam Radio playlist created using this script: https://open.spotify.com/playlist/3nSxhy304kVPZz4V7OHmHe?si=ECrck2GxSluUZtXK11KiNQ

## Let's go! 

Requirements: 
* Python 3.x (tested with python3.7)
* [`spotipy`](https://spotipy.readthedocs.io/en/2.9.0/)
* [`selenium`](https://pypi.org/project/selenium/)
* [`geckodriver`](https://github.com/mozilla/geckodriver/releases). Make sure you specify the absolute path to your geckodriver file in the `mock_credentials.py` file.

Assuming you already have an account with Spotify (premium or not), you'll need to register an app with them ([see here](https://developer.spotify.com/dashboard/applications), which will take you a whole two minutes). Make sure you set your app's redirect URI to `http://localhost/`. In return, you will be given a client ID and a client secret, which you will want to put into `mock_credentials.py`; this will authorize the various calls that you'll make to the Spotify API. You will also need to input your Spotify username into the `mock_credentials.py` file, and change the name of `mock_credentials.py` to `credentials.py`.

## Note: Need to specify playlist name in the credentials file

Now, in the command-line of your local machine, run `python3.x generate_refresh_token.py`. This will open up a browser page, so make sure you're on a machine that has a browser with GUI (i.e. not an Always Free Oracle server). Follow the instructions in the command line and a refresh token will be given to you, which you will need to put into `credentials.py`. This will prevent you from having to re-identify with the Spotify API every hour or so, thus enabling the script to run indefinitely.

Finally, create a playlist called "Djam Radio" in Spotify (case-sensitive), which is where the songs will be dumped.

You now have everything for your script to run on your machine, by running the `python3.x ubuntu_server_radio_downloader.py`. The script will also dump the name of the songs in the file `list_of_songs.txt`. Occasionally, some songs played on this radio are not available through Spotify, in which case the song name will be recorded in the file `reject_songs.txt`.

I recommend setting up a [free server](https://www.oracle.com/cloud/free/#always-free) and running this script on there. Note that an oracle Always Free ubuntu server will require installation of python and the dependencies listed above. Assuming all of the dependencies have been installed, the script can be run indefinitely using the `nohup python3.x ubuntu_server_radio_downloader.py` command, which will prevent the process from crashing when you disconnect from the server.





