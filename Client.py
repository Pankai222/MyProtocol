import socket
from threading import *
import time
from configparser import ConfigParser
import re

conf = ConfigParser()
conf.read("opt.conf")

# create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# setting available idle time for socket
server_address = ('localhost', 43098)
print('Connecting to server...\n')

client_ip = socket.gethostbyname(socket.gethostname())
# creating a mutable list for stopping write()-function
_START = [True, True]
global server_counter
global counter


def handshake():
    handshake_counter = 0
    while True:
        try:
            sock.settimeout(10)
            sock.sendto(('com-{} '.format(handshake_counter) + client_ip).encode(), server_address)
            print('com-{} '.format(handshake_counter) + client_ip)
            # calls recvfrom() method and divides the arguments into 2 variables,
            # accept for the data received and server for the connection information
            request, server = sock.recvfrom(4096)
            if request.decode().startswith('com-0 accept ' + client_ip):
                print(request.decode())
                sock.sendto('com-{} accept'.format(handshake_counter).encode(), server_address)
                print('com-{} accept'.format(handshake_counter))
                break
            else:
                print('No accept received, closing connection...')
                _START[0] = False
                break
        except socket.timeout:
            print('No connection found')


# background-thread that listens for datagram-messages and error-codes from server and prints to client
def read():
    global server_counter
    server_counter = 0
    try:
        while _START[0]:
            data, server = sock.recvfrom(4096)
            server_counter = int(re.search(r"\d+", data.decode()).group())
            if data.decode().endswith('con-h 0x00'):
                continue
            elif data.decode().endswith('Package incomplete'):
                print('Error in data transfer, closing connection....')
                break
            elif data.decode().endswith('Package limit reached'):
                print(data.decode() + ', closing connection...')
                break
            elif data.decode() == 'con-res 0xFE':
                sock.sendto(b'con-res 0xFE', server_address)
                print('\n' + data.decode() + ' received. Your next input will close the program.')
                break
            elif data.decode().endswith('END'):
                break
            print(data.decode())
            time.sleep(0.1)
    except socket.timeout:
        print('connection closed')
    _START[0] = False


# function that waits for input from user, prints it out, then sends to server in format according to protocol
def write():
    global counter
    # ensures that counter will not reset to 0 after automated messages if they're active.
    if _START[1] is True:
        counter = 0
    try:
        while _START[0]:
            print('\nenter message: ', end='')
            message = ('msg-{}='.format(counter) + input()).encode()
            print(message.decode())
            sock.sendto(message, server_address)
            time.sleep(0.1)
            counter = server_counter + 1

    except KeyboardInterrupt:
        print('\nclosing connection...')

    except NameError:
        print('connection has been closed')

    finally:
        sock.close()


# reads from config-file and sends message every 3 seconds if keep_alive is set to True
def keep_alive():
    message = 'con-h 0x00'.encode()
    try:
        if conf.getboolean("client", "KeepALive"):
            while True:
                time.sleep(3)
                sock.sendto(message, server_address)

    except KeyboardInterrupt:
        print('')


def bypass_handshake():
    if conf.getboolean("client", "HandshakeByPass"):
        sock.sendto(b'com-0', server_address)


def automated_message():
    global counter
    global server_counter
    counter = 0
    # sends large number of messages if automated_messages is set to True in config
    try:
        if conf.getboolean("client", "AutomatedMessages"):
            _START[1] = False
            for i in range(conf.getint("client", "PackagesInAutomation")):
                if _START[0] is False:
                    break
                message = '\nmsg-{}=automated message'.format(counter).encode()
                sock.sendto(message, server_address)
                print(message.decode())
                time.sleep(0.1)
                counter = server_counter + 1
    except AttributeError:
        print('connection has been closed')


def ddos():
    global counter
    global server_counter
    counter = 0
    if conf.getboolean("client", "DDoS"):
        for i in range(26):
            message = '\nmsg-{}=message flooood'.format(counter).encode()
            sock.sendto(message, server_address)
            print(message.decode())
            data, server = sock.recvfrom(4096)
            server_counter = int(re.search(r"\d+", data.decode()).group())
            print(data.decode())
            counter = server_counter + 1


bypass_handshake()
handshake()
ddos()
t1 = Thread(target=read)
t1.daemon = True
t2 = Thread(target=keep_alive)
t2.daemon = True
t1.start()
t2.start()
automated_message()
write()
