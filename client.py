import os
import socket
import time
import keyboard
from getmac import get_mac_address as gma
from sys import argv

is_admin = False

COLOR = {
    'RED'                : '\033[1;91m',
    'UNDERLINE_PURPLE'   : '\033[4;34m',
    'GREEN'              : '\033[1;92m',
    'YELLOW'             : '\033[1;33m',
    'CYAN'               : '\033[0;36m',
    'PURPLE'             : '\033[0;34m',
    'MAGENTA'            : '\033[0;35m',
    'DEFAULT'            : '\033[0m',
    'TWITTER_BLUE'       : '\033[38;5;33m',
}

def get_ip():
    """
    Gets my current IP address (Locally)
    :return: IP Address
    :rtype: str
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def translate_repsonse(server_response):
    """
    Function to translate the Server-to-Client protocol into the correct value
    :param server_response: The message received from server
    :type server_response: str
    :return: a Tuple with the value and Message (if there is one)
    :rtype: tuple
    """
    special_types = ['STR', 'CLEAR', 'QUIT', 'SHT', 'PLAY', 'CNFG']
    t = server_response[0:6].strip()
    if t not in special_types:
        msg, content = server_response[7:].split("|")
    else:
        content = server_response[7:]
    match(t):
        case 'INT':
            return int(content)
        case 'BOOL':
            return bool(int(content))
        case 'LIST':
            my_list = content.split(",")
            print(msg)
            print_list(my_list)
        case 'LYRICS':
            print_lyrics(msg, content)
        case 'STR':
            print(content)
        case 'ADMIN':
            global is_admin
            is_admin = bool(int(msg))
            print(content)
        case 'PLAY':
            return content
        case 'CLEAR':
            os.system('cls')
            print(content)
        case 'SHT' | 'QUIT' | 'CNFG':
            return content

def print_list(client_list):
    """
    Function to print a list of items
    :param client_list: A list (albums, songs, etc.)
    :type client_list: list
    :return: None
    """
    counter = 1
    for item in client_list:
        print(("      %2d) %s" % (counter,item)))
        counter += 1
    print()

def print_lyrics(songname, lyrics):
    """
    Function to print the song's lyrics
    :param songname: Name of the Song
    :param lyrics: Song's Lyrics
    :type songname: str
    :type lyrics: str
    :return: None
    """
    print("\n      " + COLOR['TWITTER_BLUE'] + songname.title() + " - Pink Floyd" + COLOR['DEFAULT'])
    if len(lyrics) > 0:
        for line in lyrics.split("\n"):
            if line.startswith("[") and line.endswith("]"):
                print()
            print("      " + line)
    else:
        print("This song is instrumental")

def client_to_server(my_socket):
    """
    Manages the Client-to-Server dialog
    :param my_socket: Client-to-Server socket
    :type my_socket: socket obj
    :return: None
    """
    while True:
        msg = input((COLOR['TWITTER_BLUE'] + 'PFD> ' if not is_admin else COLOR['GREEN'] + 'PFD# ') + COLOR['DEFAULT'])
        space = msg.find(" ")
        if space != -1:
            command = msg[0:space]
            length = len(msg[space+1:])
            content = msg[space+1:]
            msg = "%10s %4d %s" % (command, length, content)
        else:
            command = msg
            msg = "%10s %4d" % (command, 0)
        try:
            my_socket.send(msg.encode())
        except:
            print(COLOR['RED'] + "Server is no longer available" + COLOR['DEFAULT'])
            break
        data = my_socket.recv(4096).decode()
        data_type = data[0:6].strip()
        if data_type != "CNFG":
            data_content = translate_repsonse(data)

        match (data_type):
            case 'SHT':
                print(data_content)
                my_socket.close()
                break
            case 'PLAY':
                print(data_content, end='\r')
                for i in range(2, 0, -1):
                    data = my_socket.recv(1024).decode()
                    data_content = translate_repsonse(data)
                    print(data_content, end='\r')
                data = my_socket.recv(1024).decode()
                data_content = translate_repsonse(data)
                print(data_content)
            # case 'UPDATE':
            #     print(data_content)
            #     if is_admin:
            #         prompt = (COLOR['TWITTER_BLUE'] + 'PFD> ' if not is_admin else COLOR['GREEN'] + 'PFD# ') + COLOR['DEFAULT']
            #         user_input = input( prompt + "Choose method: ")
            #         msg = "%10s %4d" % ("UPDATE", int(user_input))
            #         my_socket.send(msg.encode())
            #         data = my_socket.recv(4096).decode()
            #         data_content = translate_repsonse(data)
            #         print(data_content)
            #         data = my_socket.recv(4096).decode()
            #         data_content = translate_repsonse(data)
            #         print(data_content)
            #     continue
            case 'CNFG':
                config = translate_repsonse(data)
                while(data_type == 'CNFG'):
                    if config == "":
                        data = my_socket.recv(4096).decode()
                        data_type = data[0:6].strip()
                        if data_type != 'CNFG':
                            config = translate_repsonse(data)
                            break
                        config = translate_repsonse(data)
                    user_input = input(config + " ")
                    my_socket.send(user_input.encode())
                    config = ""
            case 'QUIT':
                print(data_content)
                time.sleep(3)
                break

def main():
    # Cleans the CMD window
    os.system('cls')
    # Ask for the server's IP address
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        ip_add = input("Enter server's IP address: ")
        # If the client inputs 'my_ip' it gets the client's ip from the get_ip function
        ip_add = ip_add if ip_add != "my_ip" else get_ip()
        # Tries to connect, if fails informs that the IP address is wrong
        try:
            my_socket.connect((ip_add, 9595))
            break
        except:
            print(COLOR['RED'] + 'Wrong IP Address' + COLOR['DEFAULT'])
    # After successful connection get's the client's computer name and MAC address and sends it to the server
    # So the server can recognize the client in it's log
    mac = gma()
    details = os.environ['COMPUTERNAME'] + "|" + mac
    my_socket.send(details.encode())
    data = my_socket.recv(1024).decode()
    os.system('cls')
                                    # msg = ""
                                    # command = None
                                    # length = None
                                    # content = None
    # Prints the Header Message
    print(data)
    # Start the Client-to-Server dialog
    client_to_server(my_socket)
    # Closing the client's socket and informing the client
    my_socket.close()
    print("Disconnected from server\nPress "+COLOR['GREEN'] + "[SPACE]" + COLOR['DEFAULT']+ " to exit")
    # Waiting for SPACE to be pressed (So the window won't close instantly)
    keyboard.wait('space')

if __name__ == "__main__":
    main()