import schedule
import time
import server_radio_downloader
from datetime import datetime



if __name__ == '__main__':

    USER = server_radio_downloader.RadioDownloader()
    server_radio_downloader.tracks = set()

    # First check if we have the correct playlist name before anything starts
    # If not, create the new playlist with month and year
    USER.check_playlist_name()

    # This first job is to check if we ought to be changing the name of the
    # playlist
    schedule.every().hour.at('00:00').do(USER.check_playlist_name)

    # This second job is the actual scraper
    schedule.every().minute.do(USER.djam_radio, 'list_of_songs.txt')

    while True:
        schedule.run_pending()
        time.sleep(1)
