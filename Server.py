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
print('starting up on {} port {}\n'.format(*server_address))
sock.bind(server_address)


def server():
    messages_received = 0
    connection = False
    stop = False
    server_counter = 0
    # listens for client syn-message and sends back accept-message; disconnects if none is received
    request, client_address = sock.recvfrom(4096)
    # checks if SYN-message from client follows protocol and has valid ip-address, then sends SYN-ACK
    try:
        if request.decode().startswith('com-0') and socket.inet_aton(request.decode().split()[1]):
            sock.sendto('com-{} accept '.format(server_counter).encode() + request.split()[1], client_address)
            handshake1 = 'connection request received from ' + request.decode().split()[1]
            handshake2 = 'accept sent to ' + request.decode().split()[1]
            print(handshake1 + '\n''' + handshake2)
            accept, client_address = sock.recvfrom(4096)
            # checks if ACK from client follows protocol then logs the handshake and starts connection
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
                log_error(client_address)
        else:
            log_error(client_address)

        last_message_time = myTime.clock()
        while connection:
            try:
                if stop:
                    sock.sendto(b'con-res 0xFE', client_address)
                # setting available idle-time for recvfrom()-function
                sock.settimeout(4.0)
                data, client_address = sock.recvfrom(4096)
                # sets client_counter via regex by searching string for one or more digits: (\d+), after a hyphen: (r"")
                # and returning it with group()
                client_counter = int(re.search(r"\d+", data.decode()).group())
                message_time = myTime.clock()
                # increments messages_received if current message has same timestamp as last message, thereby
                # counting messages per second
                if message_time == last_message_time:
                    messages_received += 1
                else:
                    messages_received = 0
                # if messages_received exceeds predefined max, sends error-message to client
                if messages_received > conf.getint('client', 'MaxPackages'):
                    server_counter = client_counter+1
                    sock.sendto('res-{}=Package limit reached, shutting down connection'.format(server_counter).encode()
                                , client_address)
                    print('package limit reached, closing connection')
                    break
                # receives heartbeat-package and sends it back
                if data.decode().endswith('con-h 0x00'):
                    print('received {} bytes from {}'.format(len(data), client_address))
                    print('message from {}: '.format(client_address) + data.decode() + '\n')
                    sock.sendto('con-h 0x00'.encode(), client_address)
                    continue
                # receives timeout-package and shuts down
                if data.decode().endswith('con-res 0xFE'):
                    print('shutting down server...')
                    break

                print('received {} bytes from {}'.format(len(data), client_address))
                print('message from {}: '.format(client_address) + data.decode() + '\n')

                # checks if client-message follows protocol by comparing it to the counter for server-message.
                # server_counter will "always" be below client_counter before server-reply has been sent
                if client_counter == 0 or server_counter == client_counter-1 and client_counter != 1:
                    server_counter = client_counter+1
                    sock.sendto(('res-{}='.format(server_counter)+'I am server').encode(), client_address)
                    last_message_time = message_time
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
        log_error(client_address)

    except IndexError:
        log_error(client_address)

    except AttributeError:
        sock.sendto('res-{}=message does not follow protocol'.format(server_counter).encode(), client_address)
        print('message does not follow protocol, closing connection...')

    finally:
        sock.close()


def save_to_file(handshake):
    log = open("handshake_log.txt", "a")
    log.write(handshake)


def log_error(client_address):
    print('failed to establish handshake, closing program...')
    save_to_file('\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' +
                 'Failed to receive accept from client\n' + 'connection has been closed\n')
    sock.sendto(b'END', client_address)


server()
