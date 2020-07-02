# Radio Downloader
## Get the songs from your favourite radio station into a Spotify playlist! 

This script was originally written to access the excellent music selection of Djam Radio (www.djamradio.com). For every track played on this radio station, the name of the artist and the name of the song is posted, live, on the website.

This lends itself well to a script that scrapes this information in real-time, stores it in memory, and dumps all of the songs into a Spotify playlist of your choice. The current version of this script will scrape music from the radio station until the user interrupts the script. At that point, it will match the data scraped from the online radio to unique Spotify song IDs. This list of song IDs will then be used to populate the desired spotify playlist.

You may wish to create a new spotify playlist to store these songs (for which the `create_spotify_playlist()` method will come in handy), or dump them in a pre-existing playlist (which you should be able to identify using `get_spotify_playlist_id()`).

## Getting started

Requirements: 
* [`spotipy`](https://spotipy.readthedocs.io/en/2.9.0/)
* [`selenium`](https://pypi.org/project/selenium/)

Assuming you already have an account with Spotify, you'll need to register an app with them ([see here](https://developer.spotify.com/dashboard/applications), which will take you a whole two minutes). In return, you will be given a client ID and a client secret, which you will want to put into `credentials.py`; this will authorize the various calls that you'll make to the Spotify API. 
