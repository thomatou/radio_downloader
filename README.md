# Radio Downloader
## Get the songs from your favourite radio station into a Spotify playlist! 

This script was originally written to access the excellent music selection of Djam Radio (www.djamradio.com). For every track played on this radio station, the name of the artist and the name of the song is posted, live, on the website.

This lends itself well to a script that scrapes this information in real-time, stores it in memory, and dumps the songs into a Spotify playlist of your choice. This script will scrape track names from the radio station indefinitely (or until the user interrupts it), and add them to the Spotify playlist in batches of 10 – to minimise the number of calls to the API. Note that the script will prevent the addition of duplicates to the playlist.

The idea here is to take advantage of [Oracle's Always Free servers](https://www.oracle.com/cloud/free/#always-free), which one can set up for, well, free, and use to run this script indefinitely, without having to keep your local machine on. You do need a credit card to set up a server, but you won't be charged for an Always Free server, which is powerful to run this script.

## Let's go! 

Requirements: 
* Python 3 (tested with python3.7)
* [`spotipy`](https://spotipy.readthedocs.io/en/2.9.0/)
* [`selenium`](https://pypi.org/project/selenium/)

Assuming you already have an account with Spotify (premium or not), you'll need to register an app with them ([see here](https://developer.spotify.com/dashboard/applications), which will take you a whole two minutes). In return, you will be given a client ID and a client secret, which you will want to put into `mock_credentials.py`; this will authorize the various calls that you'll make to the Spotify API. You will also need to input your Spotify username into the `mock_credentials.py` file. You will also need to change the name of `mock_credentials.py` to `credentials.py`.

In the command-line, run `python3.x generate_refresh_token`. This will print, in the command-line, a refresh token that you will need to put into `credentials.py`. This will prevent you from having to re-identify with the Spotify API every hour or so, thus enabling the script to run indefinitely.

Finally, create a playlist called "Djam Radio" in Spotify (case-sensitive), which is where the songs will be dumped.

You now have everything for your script to run on your machine, by running the `python3.x ubuntu_server_radio_downloader.py`. However, I recommend setting up a [free server](https://www.oracle.com/cloud/free/#always-free) and running this script on there. Note that an oracle Always Free ubuntu server will require installation of python and the dependencies listed above.





