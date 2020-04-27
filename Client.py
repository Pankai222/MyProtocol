import socket
import threading
import time
from configparser import ConfigParser

conf = ConfigParser()
conf.read("opt.conf")

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Setting available idle time for socket
server_address = ('localhost', 43098)
print('Connecting to server...\n')

client_ip = socket.gethostbyname(socket.gethostname())
# Creating a mutable list for stopping write()-function
_START = [True]
_conRES = [False]


def accept():
    counter = 0
    while True:
        try:
            sock.settimeout(10)
            print('Client Com-{}: '.format(counter) + client_ip + ' sending connection request')
            sock.sendto(client_ip.encode(), server_address)
            # calls recvfrom() method and divides the arguments into 2 variables,
            # accept for the data received and server for the connection information
            request, server = sock.recvfrom(4096)
            # split accept-message and set connected to false if first index is not 'accept'
            split = request.decode().split()
            if split[0] != 'accept':
                print('Failed to receive accept-message, closing connection...')
                break
            else:
                print('Client Com-{}: accept'.format(counter))
                print('Server Com-{}: '.format(counter) + request.decode())
                break
        except socket.timeout:
            print('No connection found, retrying...')
            accept()


def read():
    while True:
        data, server = sock.recvfrom(25)
        data_split = data.decode().split("#")
        if data_split[0] == 'con-h 0x00':
            continue
        elif data_split[0] == 'Package incomplete':
            print('Error in data transfer: {}'.format(data_split[0]))
            break
        elif data.decode() == 'con-res 0xFE':
            sock.sendto(b'con-res 0xFE', server_address)
            print('\n' + data.decode() + ' received. Your next input will close the program.')
            _conRES[0] = True
            break
        elif data_split[0] == 'END':
            break
        print('Server Response-{}: {!r}'.format(data_split[1], data_split[0]))
    _START[0] = False


def write():
    counter = 0
    try:
        while _START[0]:
            print('\nYour message: ', end='')
            message = input().encode() + b'#' + str(counter).encode()
            msg_split = message.decode().split("#")
            print('Client Message-{}: '.format(counter) + msg_split[0])
            counter += 2
            sock.sendto(message, server_address)
            if msg_split[0] == 'END':
                sock.sendto(message, server_address)
                print('Closing connection...')
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nClient closed unexpectedly')

    finally:
        sock.close()


def keep_alive():
    message = 'con-h 0x00'.encode()
    try:
        if conf.getboolean("client", "KeepALive"):
            while True:
                time.sleep(3)
                sock.sendto(message, server_address)

    except KeyboardInterrupt:
        print('')


accept()
t1 = threading.Thread(target=read)
t1.daemon = True
t2 = threading.Thread(target=keep_alive)
t2.daemon = True
t1.start()
t2.start()
write()
