import socket
import threading
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
_START = [True]
global server_counter
global counter


def accept():
    global server_counter
    global counter
    counter = 0
    server_counter = 0
    while True:
        try:
            sock.settimeout(10)
            print('com-{} '.format(counter) + client_ip)
            sock.sendto(('com-{} '.format(counter) + client_ip).encode(), server_address)
            # calls recvfrom() method and divides the arguments into 2 variables,
            # accept for the data received and server for the connection information
            request, server = sock.recvfrom(4096)
            if request.decode().startswith('com-0 accept ' + client_ip):
                print(request.decode())
                sock.sendto('com-{} accept'.format(counter).encode(), server_address)
                print('com-{} accept'.format(counter))
                break
            else:
                print('No accept received, closing connection...')
                _START[0] = False
                break
        except socket.timeout:
            print('No connection found')
            accept()


# background-thread that listens for datagram-messages and error-codes from server and prints to client
def read():
    global server_counter
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
        print('lol')
    _START[0] = False


# function that waits for input from user, prints it out in nice format, then sends to server
def write():
    global counter
    try:
        while _START[0]:
            print('\nenter message: ', end='')
            message = ('msg-{}='.format(counter) + input()).encode()
            print(message.decode())
            sock.sendto(message, server_address)
            time.sleep(0.1)
            counter = server_counter + 1
    except KeyboardInterrupt:
        print('\nConnection closed')

    except TypeError:
        print('\nError in counter')

    finally:
        sock.close()


# reads from config-file and sends message every 3 seconds if keep_alive is set to True
def keep_alive():
    message = 'con-h 0x00'.encode()
    try:
        if conf.getboolean("client", "keep_alive"):
            while True:
                time.sleep(3)
                sock.sendto(message, server_address)

    except KeyboardInterrupt:
        print('')


def bypass_handshake():
    sock.sendto(b'hello', server_address)


def ddos():
    global counter
    counter = 0
    # sends large number of messages if DDoS is set to True
    if conf.getboolean("client", "DDoS"):
        for i in range(conf.getint("client", "packages_in_DDoS")):
            message = '\nmsg-{}=hejsa'.format(counter).encode()
            sock.sendto(message, server_address)
            print(message.decode())
            data, server = sock.recvfrom(4096)
            s_counter = int(re.search(r"\d+", data.decode()).group())
            print(data.decode())
            counter = s_counter + 1
        time.sleep(0.1)


accept()
ddos()
t1 = threading.Thread(target=read)
t1.daemon = True
t2 = threading.Thread(target=keep_alive)
t2.daemon = True
t1.start()
t2.start()
write()

