import socket
import Timeclass as myTime
from configparser import ConfigParser
import re

conf = ConfigParser()
conf.read("opt.conf")
# create a UDP socket
# first argument specifies address family, second specifies socket type (in this case datagram)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# bind the socket to the port
server_address = ('localhost', 43098)
print('starting up on {} port {}'.format(*server_address))
sock.bind(server_address)


def server():
    connection = False
    stop = False
    server_counter = 0
    # listens for client syn-message and sends back accept-message; disconnects if none is received
    request, client_address = sock.recvfrom(4096)
    # checks if SYN-message from client contains correct ip-address, then sends SYN-ACK before receiving
    # final ACK from client
    try:
        if request.decode().startswith('com-0') and socket.inet_aton(request.decode().split()[1]):
            sock.sendto('com-{} accept '.format(server_counter).encode() + request.split()[1], client_address)
            handshake1 = '\nconnection request received from ' + request.decode().split()[1]
            handshake2 = 'accept sent to ' + request.decode().split()[1]
            print(handshake1 + '\n''' + handshake2)
            accept, client_address = sock.recvfrom(4096)
            if accept.decode().startswith('com-0 accept'):
                handshake3 = accept.decode().split()[1] + ' received from ' + request.decode().split()[1]
                print(handshake3 + '\n')
                final_handshake = '\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' + handshake1 + '\n[' + \
                                  myTime.get_date() + ' ' + myTime.clock() + '] '\
                                  + handshake2 + '\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' + \
                                  handshake3 + '\nconnection has been established\n'

                save_to_file(final_handshake)
                connection = True
            else:
                print('accept not received from client, closing program...')
                save_to_file('\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' +
                             'Failed to receive accept from client\n' + 'connection has been closed\n')
                sock.sendto(b'END', client_address)
        else:
            print('error in establising connection, closing program...')
            save_to_file('\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' +
                         'Failed to receive accept from client\n' + 'connection has been closed\n')
            sock.sendto(b'END', client_address)

        while connection:
            try:
                if stop:
                    sock.sendto(b'con-res 0xFE', client_address)
                # setting available idle-time for recvfrom()-function
                sock.settimeout(4.0)
                data, client_address = sock.recvfrom(4096)
                client_counter = int(re.search(r"\d+", data.decode()).group())

                if data.decode().endswith('con-h 0x00'):
                    print('received {} bytes from {}'.format(len(data), client_address))
                    print('message from {}: '.format(client_address) + data.decode() + '\n')
                    sock.sendto('con-h 0x00'.encode(), client_address)
                    continue
                if data.decode().endswith('con-res 0xFE'):
                    break
                print('received {} bytes from {}'.format(len(data), client_address))
                print('message from {}: '.format(client_address) + data.decode() + '\n')

                if client_counter == 0 or server_counter == client_counter-1\
                        and client_counter != 1:
                    server_counter = client_counter+1
                    sock.sendto(('res-{}='.format(server_counter)+'I am server').encode(), client_address)
                else:
                    print('Error in data transfer, closing connection...')
                    sock.sendto(('res-{}='.format(server_counter)+'Package incomplete').encode(), client_address)
                    break
            # throws exception if socket timeout is reached and continues loop to send stop-message to client
            except socket.timeout:
                print('socket has reached timeout')
                stop = True
                continue

    # handles exception given if program is stopped while waiting for user input
    except KeyboardInterrupt:
        print('shutting down server...')

    except OSError:
        print('error in establising connection, closing program...')
        save_to_file('\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' +
                     'Failed to receive accept from client\n' + 'connection has been closed\n')
        sock.sendto(b'END', client_address)

    finally:
        sock.close()


def save_to_file(handshake):
    log = open("handshake_log.txt", "a")
    log.write(handshake)


server()
