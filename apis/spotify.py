import os
from lxml import html
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from server import get_string

BAD_ALBUM_WORDS = [
    'live',
    'the later years',
    'delicate sound of thunder',
    'work in progress',
    'the best',
    'collection',
    'film',
    'works',
    'complete',
    'relics',
    'early',
    'shine on',
    'pulse',
    'pair',
    'julia',
    'apples',
    'arnold'
] + [i for i in "0123456789()[]"]

def containsNumber(value):
    for character in value:
        if character.isdigit():
            return True
    return False

def clean_name(name):
    found = False
    special_characters = "!@#$%^&*()-+'?_=,.<>/"
    for i in range(len(name)):
        if name[i] in special_characters:
            name = name[0:i] + name[i+1:]
            found = True
            break
    if found:
        name = clean_name(name)
    return name

def get_lyrics_from_web(songname):
    uri = f'https://genius.com/Pink-floyd-{"-".join(clean_name(songname).split(" ")).lower()}-lyrics'
    page = requests.get(uri)
    tree = html.fromstring(page.content)
    ID = tree.xpath("/html/body/div[1]/main/div[2]/div[2]/div[2]/div/div[not(contains(@class, 'ShareButtons__Root-jws18q-0')) "
                    "and not(contains(@class, 'Lyrics__Footer-sc-1ynbvzw-2')) ]//text()")
    lyrics = ""
    for i in ID:
        lyrics += i + "\n"
    return lyrics

def is_an_album(album):
    albums = os.listdir('data/albums_genius')
    if album in albums:
        songs = os.listdir('data/albums_genius/' + album)
        return len(songs)
    return 0

def get_all_albums(client_id, client_secret):
    lz_uri = 'spotify:artist:0k17h0D3J5VfsdmQ1iZtE9'
    spotify = spotipy.Spotify(
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id,
                                                            client_secret=client_secret))
    results = spotify.artist_albums(lz_uri, album_type='album', limit='50', offset='0')
    albums = results['items']
    while results['next']:
        results = spotify.next(results)
        albums.extend(results['items'])

    new_albums = []
    for album in albums:
        if (not any(word in album['name'].lower() for word in BAD_ALBUM_WORDS) and album['album_type'] == 'album'):
            new_albums.append(album)
    albums = new_albums

    new_albums = []
    album_names = list(dict.fromkeys([album['name'] for album in albums]))
    for album in albums:
        if album['name'] in album_names:
            new_albums.append(album)
            album_names.remove(album['name'])

    albums = new_albums
    return (spotify, albums)

def get_album_names(client_id, client_secret):
    spotify , albums = get_all_albums(client_id, client_secret)
    album_names = []
    for album in albums:
        album_names.append(album['name'])
    return ",".join(album_names)

def get_tracks(album, spotify):
    lz_uri = 'spotify:album:'+album['id']
    results = spotify.album_tracks(lz_uri, limit='50', offset='0')
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])

    for track in tracks:
        splited_name = track['name'].split(":")
        if len(splited_name) > 1:
            track['name'] = splited_name[1].strip()

    for track in tracks:
        if "(" in track['name']:
            index = track['name'].index('(')
            track['name'] = track['name'][0:index].strip()

    return tracks

def get_song_length(songname, client_id, client_secret):
    spotify, albums = get_all_albums(client_id=client_id, client_secret=client_secret)
    for album in albums:
        tracks = get_tracks(album, spotify)
        for track in tracks:
            if track['name'].lower() == songname.lower():
                return (int(track['duration_ms']) / 1000)
    return -1

def get_album_by_song(songname):
    for album in os.listdir('data/albums_genius'):
        songs = [i.replace(".txt", "").lower() for i in os.listdir('data/albums_genius/'+ album)]
        if songname.lower() in songs:
            return album
    return -1

def get_song_names(album):
    path = "data/albums_genius/" + album
    if os.path.exists(path):
        all_songs = [i.replace(".txt", "") for i in os.listdir(path)]
        return ",".join(all_songs)
    else:
        return "-1"

def get_album_length(album_name,client_id, client_secret):
    spotify, albums = get_all_albums(client_id, client_secret)
    current_album = None
    for album in albums:
        if album['name'] == album_name:
            current_album = album
            break
    if current_album != None:
        tracks = get_tracks(current_album, spotify)
        sum = 0
        for track in tracks:
            sum += int(track['duration_ms'])
        return sum/1000
    else:
        return -1

def create_folder(album, spotify):
    if not os.path.exists("data/albums_spotify/" + album['name']):
        os.mkdir("data/albums_spotify/" + album['name'])
    tracks = [clean_name(i['name']) for i in get_tracks(album, spotify)]
    for track in tracks:
        song_path = "data/albums_spotify/" + album['name'] + "/" + track + ".txt"
        if "live" not in track.lower():
            if not os.path.exists(song_path):
                with open(song_path, 'w') as f:
                    f.write(get_lyrics_from_web(track))

def get_lyrics(songname):
    lyrics = None
    list_of_folders = list(os.listdir("data/albums_genius"))
    for folder in list_of_folders:
        path = "data/albums_genius/" + folder + "/" + songname.title() + ".txt"
        if os.path.exists(path):
            with open(path, 'r') as f:
                lyrics = f.read()
    return lyrics

def get_songs_by_lyrics(lyrics):
    songs_list = []
    folders = os.listdir("data/albums_genius")
    for folder in folders:
        songs = os.listdir("data/albums_genius/" + folder)
        for song in songs:
            path = "data/albums_genius/"+folder+"/"+song
            with open(path, 'r') as f:
                if lyrics.lower() in f.read().lower():
                    songs_list.append(song.replace(".txt", ""))
    return ",".join(songs_list)

def update_db(client_id, client_secret):
    print(get_string('SPOTIFY', 'Getting all albums information...'))
    spotify, pink_floyd_albums = get_all_albums(client_id, client_secret)
    print(get_string('SPOTIFY', 'Working on lyrics...'))
    for album in pink_floyd_albums:
        create_folder(album, spotify)
    print(get_string('SPOTIFY', 'Done updating!'))

def main():
    pass

if __name__ == "__main__":
    main()