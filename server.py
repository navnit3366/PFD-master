import hashlib
import socket
import os
import time
import json
import _thread
from datetime import datetime

ADMINISTRATOR_PASSWORD = "9558aa73803ae90e3a742067cbe02f11"
SERVER_CONFIG = {}
PASUE_SERVICE = False


def update_config():
    global SERVER_CONFIG
    with open('config.json', 'w') as f:
        f.write(json.dumps(SERVER_CONFIG, indent=4))


def get_config():
    global SERVER_CONFIG
    if not os.path.exists("config.json"):
        SERVER_CONFIG = {
            'admin_pass': '90b9aa7e25f80cf4f64e990b78a9fc5ebd6cecad',
            'update_method': 'genius',
            'genius_token': 'ADD HERE',
            'youtube_token': 'ADD HERE',
            'spotify_id': 'ADD HERE',
            'spotify_secret': 'ADD HERE'
        }
        with open('config.json', 'w') as f:
            f.write(json.dumps(SERVER_CONFIG, indent=4))
    else:
        with open('config.json', 'r') as f:
            SERVER_CONFIG = json.loads(f.read())


def get_ip():
    """
    Gets my current IP address (Locally)
    :return: IP Address
    :rtype: str
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def send_to_client(client_socket, t, value):
    """
    Manages the Server-to-Client protocol
    :param client_socket: Current Client
    :param t: Type of Message
    :param value: Message
    :type client_socket: socket obj
    :type t: str
    :type value: str
    :return: None
    """
    msg = "%6s %s" % (t, value)
    client_socket.send(msg.encode())


def get_string(t, msg, name=None, mac=None):
    """
    Formats the message into the right format
    and gives it the right colors depending on the message's title(sender)
    For example:
    SERVER> Hello World!
    :param t: Type of Sender (Title)
    :param msg: Message
    :param name: Name of Client
    :param mac: Client's MAC Address
    :type t: str
    :type msg: str
    :type name: str
    :type mac: str
    :return: Formatted String
    :rtype: str
    """
    final_msg = ""
    match t:
        case 'ERROR':
            final_msg += color['RED']
        case 'PFD':
            final_msg += color['TWITTER_BLUE']
        case "CLIENT":
            final_msg += color['MAGENTA']
        case 'SERVER':
            final_msg += color['GREEN']
        case 'ADMIN':
            final_msg += color['YELLOW']
        case 'INFO':
            final_msg += color['YELLOW']
        case 'SPOTIFY':
            final_msg += color['BLACK'] + color['GREENBG']
        case 'GENIUS':
            final_msg += color['BLACK'] + color['YELLOWBG']
    if name is not None:
        final_msg += t + " | " + name + " (" + mac + ")>" + color['DEFAULT'] + " " + msg
    else:
        final_msg += t + ">" + color['DEFAULT'] + " " + msg
    return final_msg


def disconnect_clients(LISTENING_SOCKET, clients):
    """
    Informs all connected client that the server is shutting down
    :param LISTENING_SOCKET: Server's listening socket
    :param clients: List of connected clients
    :type LISTENING_SOCKET: socket obj
    :type clients: list
    :return: None
    """
    for client in clients:
        send_to_client(client, 'SHT', get_string('SERVER', 'Shutting down...'))
    LISTENING_SOCKET.close()


def serve_client(client_socket, LISTENING_SOCKET, clients):
    """
    This function manages all the Server-to-Client interaction

    This function is called by multiple threads in order to server
    multiple clients at once

    :param client_socket: The Client's Socket
    :param LISTENING_SOCKET: Server's Listening Socket
    :param clients: An array of connected clients
    :return: None
    """
    global PASUE_SERVICE
    global SERVER_CONFIG
    is_admin = False
    initial_data = client_socket.recv(1024).decode()
    initial_data = initial_data.split("|")
    CLIENT_NAME = initial_data[0]
    MAC_ADDRESS = initial_data[1]
    print(get_string('SERVER', f'Client "{CLIENT_NAME}" ({MAC_ADDRESS}) connected successfully'))
    client_socket.send(WELCOME_MSG.encode())

    while True:
        if not PASUE_SERVICE:
            title = 'CLIENT' if not is_admin else 'ADMIN'
            #  Checking if the client didn't closed his window
            try:
                data = client_socket.recv(1024).decode()
            except ConnectionResetError:
                print(get_string('SERVER', f'Client "{CLIENT_NAME}" ({MAC_ADDRESS}) disconnected (CLOSED WINDOW)'))
                _thread.exit()
            except ConnectionAbortedError:
                _thread.exit()

            command = data[0:10].upper().strip()
            try:
                length = int(data[11:15])
            except:
                send_to_client(client_socket, 'STR',
                               get_string('ERROR', "Bad command format\n") + get_string('INFO', "Please type 'HELP' "
                                                                                                "to see available "
                                                                                                "commands"))
                print(get_string('ERROR', "Bad command inserted: " + data, CLIENT_NAME, MAC_ADDRESS))
                continue

            content = data[16:16 + length]
            print(get_string(title, (data.upper() if not 'GOADMIN' in data.upper() else data[:16] + ("*" * len(data[16:16 + length]))), CLIENT_NAME, MAC_ADDRESS))

            match (command):
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # --------------------------------------- Albums Commands --------------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case 'GETALBUMS':
                    msg = color['TWITTER_BLUE'] + "\n\tAll Pink Floyd's Albums: " + color['DEFAULT']
                    send_to_client(client_socket,"LIST", msg + "|" + spotify.get_album_names(SERVER_CONFIG['spotify_id'],SERVER_CONFIG['spotify_secret']))
                case 'FINDALBUM':
                    if len(content) > 0:
                        songs = spotify.is_an_album(content.title())
                        msg = ""
                        if songs == 0:
                            msg = get_string('ERROR', content.title() + " isn't an Pink Floyd Album")
                        else:
                            msg = get_string('PFD', color['TWITTER_BLUE'] + content.title() + color[
                                'DEFAULT'] + " is an Pink Floyd Album containing " + str(songs) + " songs")
                        send_to_client(client_socket,"STR", msg)
                    else:
                        send_to_client(client_socket, 'STR',
                                       get_string('ERROR', 'Syntax Error: ' + command + " [Name of Album]"))
                case 'ALBUMDUR':
                    if len(content) > 0:
                        time_in_seconds = spotify.get_album_length(content.title(), SERVER_CONFIG['spotify_id'],SERVER_CONFIG['spotify_secret'])
                        msg = ""
                        if time_in_seconds != -1:
                            t = datetime.fromtimestamp(time_in_seconds)
                            t = t.strftime("%H:%M:%S")
                            msg = get_string('PFD', "'" + content.title() + "' total duration: " + t)
                        else:
                            msg = get_string('ERROR', "No such album named '" + content.title() + "'")
                        send_to_client(client_socket,'STR', msg)
                    else:
                        send_to_client(client_socket, 'STR',
                                       get_string('ERROR', 'Syntax Error: ' + command + " [Name of Album]"))
                case 'LISTSONGS':
                    if len(content) > 0:
                        all_songs = spotify.get_song_names(content.title())
                        msg = color['TWITTER_BLUE'] + "\n\tAll Songs in '" + content.title() + "' Album: " + color['DEFAULT']
                        if all_songs != "-1":
                            send_to_client(client_socket,'LIST', msg + "|" + all_songs)
                        else:
                            send_to_client(client_socket,'STR', get_string('ERROR', "No such album named '" + content.title() + "'"))
                    else:
                        send_to_client(client_socket, 'STR',
                                       get_string('ERROR', 'Syntax Error: ' + command + " [Name of Album]"))
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # ---------------------------------------- Songs Commands --------------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case 'FINDSONG':
                    if len(content) > 0:
                        album = spotify.get_album_by_song(content)
                        if album != -1:
                            msg = get_string('PFD', "'" + content.title() + "' is a Pink Floyd song in the album '" + album + "'")
                        else:
                            msg = get_string('ERROR', "'"+ content.title() + "' isn't a Pink Floyd song")
                        send_to_client(client_socket, 'STR', msg)
                    else:
                        send_to_client(client_socket, 'STR',
                                   get_string('ERROR', 'Syntax Error: ' + command + " [Name of Song]"))
                case 'HOWLONG':
                    if len(content) > 0:
                        time_in_seconds = spotify.get_song_length(content,SERVER_CONFIG['spotify_id'],SERVER_CONFIG['spotify_secret'])
                        if time_in_seconds != -1:
                            ti = datetime.fromtimestamp(time_in_seconds)
                            ti = ti.strftime("%M:%S")
                            msg = get_string('PFD', "'" + content.title() + "' duration is " + ti)
                        else:
                            msg = get_string('ERROR', "'" + content.title() + "' isn't a Pink Floyd song")
                        send_to_client(client_socket, 'STR', msg)
                    else:
                        send_to_client(client_socket, 'STR',
                                       get_string('ERROR', 'Syntax Error: ' + command + " [Name of Song]"))
                case 'GETLYRICS':
                    if len(content) > 0:
                        lyrics = spotify.get_lyrics(content)
                        if lyrics == None:
                            msg = get_string('ERROR', "No such song called '"+ content.title() +"'")
                            send_to_client(client_socket, "STR", msg)
                        else:
                            send_to_client(client_socket, "LYRICS", content.title() + "|" + lyrics)
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', 'Syntax Error: '+ command + " [Name of Song]"))
                case 'PLAY':
                    if len(content) > 0:
                        is_a_song = True if spotify.get_album_by_song(content) != -1 else False
                        if is_a_song:
                            for i in range(3, 0, -1):
                                send_to_client(client_socket, 'PLAY', get_string('PFD', 'Song will be played in ' + str(i)))
                                time.sleep(1)
                            send_to_client(client_socket, 'PLAY', get_string('PFD', 'Enjoy ' + content.title() + ' by Pink Floyd...'))
                            youtube.play_song(content.lower(), SERVER_CONFIG['youtube_token'])
                        else:
                            send_to_client(client_socket, 'STR', get_string('ERROR', content.title() + ' is not a Pink Floyd song'))
                    else:
                        send_to_client(client_socket, 'STR',
                                       get_string('ERROR', 'Syntax Error: ' + command + " [Name of Song]"))
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # --------------------------------------- Lyrics Commands --------------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case 'FINDLYRICS':
                    if len(content) > 0:
                        songs = spotify.get_songs_by_lyrics(content)
                        if len(songs) > 0:
                            msg = "\n\t" + color['TWITTER_BLUE'] + "Song names with the lyrics: '" + content + "' in them" + color['DEFAULT']
                            send_to_client(client_socket,"LIST", msg + "|" + songs)
                        else:
                            send_to_client(client_socket, 'STR', get_string('ERROR', "No songs found with the lyrics: " + content))
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', 'Syntax Error: '+ command + " [Lyrics]"))
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # ------------------------------------------ Utility Commands ----------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case 'HELP':
                    send_to_client(client_socket,'STR', HELP_SCREEN + (ADMIN_HELP if is_admin else ""))
                case 'CLEAR':
                    send_to_client(client_socket, 'CLEAR', WELCOME_MSG)
                case 'QUIT':
                    send_to_client(client_socket, 'QUIT', get_string('PFD', 'Disconnecting from server...'))
                    print(get_string('SERVER', CLIENT_NAME + " (" + MAC_ADDRESS + ") is disconnected"))
                    clients.remove(client_socket)
                    time.sleep(3)
                    break
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # -------------------------------------- Administrator Commands --------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case 'GOADMIN':
                    if len(content) > 0:
                        if not is_admin:
                            md5 = hashlib.md5(content.encode()).hexdigest()
                            sha1 = hashlib.sha1(md5.encode()).hexdigest()
                            if sha1 == SERVER_CONFIG['admin_pass']:
                                print(get_string('ADMIN', 'Logged in as Administrator', CLIENT_NAME, MAC_ADDRESS))
                                send_to_client(client_socket,"ADMIN", "1|"+get_string('SERVER', 'You now have Administrator privileges'))
                                is_admin = True
                            else:
                                send_to_client(client_socket,"ADMIN", "0|"+get_string('ERROR', 'Wrong password'))
                        else:
                            send_to_client(client_socket, 'STR', get_string('ERROR', "You already have Administrator privileges"))
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', 'Syntax Error: '+ command + " [Password]"))
                case 'UPDATE':
                    if is_admin:
                        PASUE_SERVICE = True
                        if SERVER_CONFIG['update_method'] == 'genius':
                            genius.update_db(force_update=True, token=SERVER_CONFIG['genius_token'])
                        else:
                            spotify.update_db(SERVER_CONFIG['spotify_id'],SERVER_CONFIG['spotify_secret'])
                        send_to_client(client_socket, 'STR', get_string('SERVER', 'Database has been updated successfully!'))
                        PASUE_SERVICE = False
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', "You don't have Administrator privileges"))
                case 'GOUSER':
                    if is_admin:
                        is_admin = False
                        send_to_client(client_socket,'ADMIN', '0|'+ get_string('SERVER', 'You no longer have Administrator privileges'))
                    else:
                        send_to_client(client_socket,'STR', get_string('ERROR', "You don't have Administrator privileges"))
                case 'SCLEAR':
                    if is_admin:
                        os.system('cls')
                        print(get_string('ADMIN', 'Cleared the log', CLIENT_NAME, MAC_ADDRESS))
                        msg = get_string('SERVER', 'Log cleared')
                    else:
                        msg = get_string('ERROR', "You don't have Administrator privileges")
                    send_to_client(client_socket, 'STR', msg)
                case 'SHUTDOWN':
                    if is_admin:
                        disconnect_clients(LISTENING_SOCKET, clients)
                        exit()
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', "You don't have Administrator privileges"))
                case 'SET':
                    if is_admin:
                        admin_choice = content.upper()
                        match (admin_choice):
                            case 'PASS':
                                send_to_client(client_socket, 'CNFG', get_string('SERVER', 'Enter old password:'))
                                data = client_socket.recv(1024).decode()
                                md5 = hashlib.md5(data.encode()).hexdigest()
                                sha1 = hashlib.sha1(md5.encode()).hexdigest()
                                if sha1 == SERVER_CONFIG['admin_pass']:
                                    send_to_client(client_socket, 'CNFG', get_string('SERVER', 'Enter new password:'))
                                    data = client_socket.recv(1024).decode()
                                    md5 = hashlib.md5(data.encode()).hexdigest()
                                    sha1 = hashlib.sha1(md5.encode()).hexdigest()
                                    SERVER_CONFIG['admin_pass'] = sha1
                                    send_to_client(client_socket, 'STR', get_string('SERVER', 'Password changed successfully!'))
                                    update_config()
                                    print(get_string(title, 'Changed the Administrator password', CLIENT_NAME, MAC_ADDRESS))
                                else:
                                    send_to_client(client_socket, 'STR', get_string('ERROR', 'Wrong password'))
                            case 'METHOD':
                                send_to_client(client_socket, 'CNFG', get_string('SERVER', 'Choose an update method (G - Genius, S - Spotify):'))
                                data = client_socket.recv(1024).decode()
                                match(data[0].upper()):
                                    case 'G':
                                        if SERVER_CONFIG['update_method'] != 'genius':
                                            SERVER_CONFIG['update_method'] = 'genius'
                                            send_to_client(client_socket, 'STR',
                                                           get_string('SERVER', 'Update method changed to Genius'))
                                            update_config()
                                        else:
                                            send_to_client(client_socket, 'STR',
                                                           get_string('ERROR', 'Update method is already Genius'))
                                    case 'S':
                                        if SERVER_CONFIG['update_method'] != 'spotify':
                                            SERVER_CONFIG['update_method'] = 'spotify'
                                            send_to_client(client_socket, 'STR',
                                                           get_string('SERVER', 'Update method changed to Spotify'))
                                            update_config()
                                        else:
                                            send_to_client(client_socket, 'STR',
                                                           get_string('ERROR', 'Update method is already Spotify'))
                                    case _:
                                        send_to_client(client_socket, 'STR', get_string('ERROR', 'Syntax Error: SET METHOD [G/S]'))
                            case 'HELP':
                                send_to_client(client_socket, 'STR', get_string('STR', SET_HELP))
                            case _:
                                send_to_client(client_socket, 'STR', get_string('ERROR', 'Syntax Error: SET [COMMAND], try: SET HELP for more information'))
                    else:
                        send_to_client(client_socket, 'STR', get_string('ERROR', "You don't have Administrator privileges"))
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                # ----------------------------------------- Unknown Command ------------------------------------------------
                # //////////////////////////////////////////////////////////////////////////////////////////////////////////
                case _:
                    send_to_client(client_socket,"STR", get_string('ERROR', "Command '" + color['RED'] + command + color[
                        'DEFAULT'] + "' is unknown!") + "\n" +
                                   get_string('ERROR', "Use 'HELP' to see available commands"))
    client_socket.close()


from apis import genius, spotify, youtube

color = {
    'RED'                : '\033[1;91m',
    'UNDERLINE_PURPLE'   : '\033[4;34m',
    'GREEN'              : '\033[1;92m',
    'YELLOW'             : '\033[1;33m',
    'CYAN'               : '\033[0;36m',
    'PURPLE'             : '\033[0;34m',
    'MAGENTA'            : '\033[0;35m',
    'DEFAULT'            : '\033[0m',
    'TWITTER_BLUE'       : '\033[38;5;33m',
    'WHITEFG'            : '\033[97m',
    'GREENBG'            : '\033[102m',
    'BLACK'              : '\033[30m',
    'YELLOWBG'           : '\033[43m'
}

WELCOME_MSG = rf"""{color['MAGENTA']}
        __________.__        __     ___________.__                   .___
        \______   \__| ____ |  | __ \_   _____/|  |   ____ ___.__. __| _/
         |     ___/  |/    \|  |/ /  |    __)  |  |  /  _ <   |  |/ __ | 
         |    |   |  |   |  \    <   |     \   |  |_(  <_> )___  / /_/ | 
         |____|   |__|___|  /__|_ \  \___  /   |____/\____// ____\____ | 
                          \/     \/      \/                \/         \/ {color['DEFAULT']}
                          
                                Discography Server
               ___________________________________________________
              |                                                   |
              |             Type {color['MAGENTA']}'HELP'{color['DEFAULT']} to see commands           |
              |___________________________________________________|
        
                  """

HELP_SCREEN = f"""{color['TWITTER_BLUE']}Hello and Welcome to the Pink Floyd Discography Manager! {color['DEFAULT']}
In here you can ask the server for information about Pink Floyd
{color['YELLOW']}Commands that can be used:
{"%38s - %s" % (color['RED'] + "GETALBUMS" + color['DEFAULT'], "Display all albums of the band")}
{"%45s - %s" % (color['RED'] + "FINDALBUM " + color['YELLOW'] + "[Name of Album]" + color['DEFAULT'], "Check if an album is by Pink Floyd")}
{"%45s - %s" % (color['RED'] + "ALBUMDUR " + color['YELLOW'] + "[Name of Album]" + color['DEFAULT'], "Get the length of an album")}
{"%45s - %s" % (color['RED'] + "LISTSONGS " + color['YELLOW'] + "[Name of Album]" + color['DEFAULT'], "Display a list of songs in an album")}
{"%45s - %s" % (color['RED'] + "FINDSONG " + color['YELLOW'] + "[Name of Song]" + color['DEFAULT'], "Check if a song is by Pink Floyd")}
{"%45s - %s" % (color['RED'] + "HOWLONG " + color['YELLOW'] + "[Name of Song]" + color['DEFAULT'], "Display the length of a song")}
{"%45s - %s" % (color['RED'] + "GETLYRICS " + color['YELLOW'] + "[Name of Song]" + color['DEFAULT'], "Display the song's lyrics")}
{"%45s - %s" % (color['RED'] + "FINDLYRICS " + color['YELLOW'] + "[Lyrics]" + color['DEFAULT'], "Display a list of songs contains the specified lyrics")}
{"%38s - %s" % (color['RED'] + "CLEAR" + color['DEFAULT'], "Clean the screen")}
{"%38s - %s" % (color['RED'] + "QUIT" + color['DEFAULT'], "Exit the program")}

{color['RED']}GOADMIN [PASSWORD] - BE CAREFUL IF YOU DON'T HAVE PERMISSIONS DON'T TRY TO GO ADMIN
"""

ADMIN_HELP = f"""
{color['GREEN']} Administrator Commands:
{"%31s - %s" % ("UPDATE" + color['DEFAULT'], "Update the Pink Floyd Database (Takes few minutes)")}
{"%38s - %s" % (color['GREEN'] + "SHUTDOWN" + color['DEFAULT'], "Shutdown the server")}
{"%38s - %s" % (color['GREEN'] + "SCLEAR" + color['DEFAULT'], "Clean the server log")}
{"%38s - %s" % (color['GREEN'] + "SET" + color['DEFAULT'], "Change server settings")}
{"%38s - %s" % (color['GREEN'] + "GOUSER" + color['DEFAULT'], "Go back to User Privileges")}
"""

SET_HELP = f"""
{color['GREEN']} Avaliable SET Commands:
{"%31s - %s" % ("SET METHOD" + color['DEFAULT'], "Set update method for database")}
{"%38s - %s" % (color['GREEN'] + "SET PASS" + color['DEFAULT'], "Change Administrator Password")}
"""


def main():
    get_config()
    # Cleans the screen
    os.system('cls')
    # Checks if there's a database, if no, creates it
    if not os.path.exists('data/albums_genius'):
        print(get_string('SERVER', 'Building database for the first time...'))
        os.mkdir('data/albums_genius')
        genius.update_db(SERVER_CONFIG['genius_token'], force_update=True)
    os.system('cls')
    # Opening the listening socket and informs that the server is up and running
    LISTENING_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(get_string('SERVER', 'Server is ready for clients'))
    server_address = ("", 9595)
    LISTENING_SOCKET.bind(server_address)
    print(LISTENING_SOCKET.getsockname())
    # Waiting for clients to connect
    LISTENING_SOCKET.listen(9)
    clients = []
    while True:
        # Accepting new clients if the listening socket is still up
        try:
            client_socket, client_address = LISTENING_SOCKET.accept()
        except:
            break
        # Adding the new client to the list of active clients
        clients.append(client_socket)
        # Starting a new thread for client so the server can serve more people simultaneously
        _thread.start_new_thread(serve_client, (client_socket, LISTENING_SOCKET, clients, ))

if __name__ == "__main__":
    main()
