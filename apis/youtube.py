import json
import os

import requests

YOUTUBE_MUSIC = 'UCO6LS_5W7vqG9mALDNzSFug'

def play_song(songname, token):
    results = requests.get(f'https://youtube.googleapis.com/youtube/v3/search?part=snippet&channelId={YOUTUBE_MUSIC}&maxResults=3&q={songname}&key={token}').json()['items']
    names = [result['snippet']['title'] for result in results]
    has_official = any('official' in name.lower() for name in names)
    for result in results:
        if result['snippet']['channelId'] == YOUTUBE_MUSIC:
            if has_official:
                if 'official' in result['snippet']['title'].lower():
                    os.system(f'start /max https://www.youtube.com/watch?v={result["id"]["videoId"]}')
                    break
            else:
                os.system(f'start /max https://www.youtube.com/watch?v={result["id"]["videoId"]}')
                break



def main():
    data = ("%10s %4d %s" % ("GOADMIN", 5, "admin"))
    length = 5
    print(data.upper() if not 'GOADMIN' in data.upper() else data[:16] + ("*" * len(data[16:16 + length])))

if __name__ == "__main__":
    main()
