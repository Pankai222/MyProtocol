import socket
import threading
import time
from configparser import ConfigParser
import Timeclass as myTime

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
                _START[0] = False
                break
            else:
                print('Client Com-{}: accept'.format(counter))
                print('Server Com-{}: '.format(counter) + request.decode())
                sock.sendto(b'accept ' + client_ip.encode(), server_address)
                print('\nWrite END to close client')
                break
        except socket.timeout:
            print('No connection found, retrying...')
            accept()


# background-thread that listens for datagram-messages and error-codes from server and prints to client
def read():
    while True:
        data, server = sock.recvfrom(4096)
        data_split = data.decode().split("<!split!>")
        if data_split[0] == 'con-h 0x00':
            continue
        elif data_split[0] == 'Package incomplete':
            print('Error in data transfer, closing connection....')
            break
        elif data_split[0] == 'Package limit reached':
            print(data_split[0] + ', closing connection...')
            break
        elif data.decode() == 'con-res 0xFE':
            sock.sendto(b'con-res 0xFE', server_address)
            print('\n' + data.decode() + ' received. Your next input will close the program.')
            break
        elif data_split[0] == 'END':
            break
        print('{} Server Response-{}: {!r}'.format(data_split[0], data_split[2], data_split[1]))
    _START[0] = False


# function that waits for input from user, prints it out in nice format, then sends to server
def write():
    counter = 0
    # sends large number of messages if message_flood is set to True
    if conf.getboolean("client", "message_flood"):
        for i in range(conf.getint("client", "packages")):
            sock.sendto(
                str(myTime.clock()).encode() + b'<!split!>' + b'message' + b'<!split!>' + str(counter).encode(),
                server_address)
            counter += 2
        time.sleep(0.1)
    try:
        while _START[0]:
            print('\nYour message: ', end='')
            # this bitch of a message contains: current time, split, user-input, split, message-counter
            message = str(myTime.clock()).encode() + b'<!split!>' + input().encode() + b'<!split!>' + \
                str(counter).encode()
            msg_split = message.decode().split("<!split!>")
            print('[{}] Client Message-{}: '.format(myTime.clock(), counter) + msg_split[1])
            counter += 2
            sock.sendto(message, server_address)
            if msg_split[1] == 'END':
                sock.sendto(message, server_address)
                print('Closing connection...')
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        print('\nClient closed unexpectedly')

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


accept()
t1 = threading.Thread(target=read)
t1.daemon = True
t2 = threading.Thread(target=keep_alive)
t2.daemon = True
t1.start()
t2.start()
write()

