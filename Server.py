import socket
import Timeclass as myTime
from configparser import ConfigParser

conf = ConfigParser()
conf.read("opt.conf")
# create a UDP socket
# first argument specifies address family, second specifies socket type (in this case datagram)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# bind the socket to the port
server_address = ('localhost', 43098)
print('Starting up on {} port {}'.format(*server_address))
sock.bind(server_address)


def server():
    connection = False
    stop = False
    counter = 1
    msg_counter = 0
    # listens for client ack-message and sends back accept-message; disconnects if none is received
    try:
        request, client_address = sock.recvfrom(4096)
        # checks if SYN-message from client contains correct ip-address, then sends SYN-ACK before receiving
        # final ACK from client
        if request.decode() == socket.gethostbyname(socket.gethostname()):
            sock.sendto(b'accept ' + request, client_address)
            handshake1 = 'connection request received from ' + request.decode()
            handshake2 = 'accept sent to ' + request.decode()
            print(handshake1 + '\n''' + handshake2)
            accept, client_address = sock.recvfrom(4096)
            handshake3 = accept.decode().split()[0] + ' received from ' + accept.decode().split()[1]
            print(handshake3)
            final_handshake = '\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' + handshake1 + '\n[' + \
                              myTime.get_date() + ' ' + myTime.clock() + '] '\
                              + handshake2 + '\n[' + myTime.get_date() + ' ' + myTime.clock() + '] ' + handshake3 + '\n'
            save_to_file(final_handshake)
            connection = True
        else:
            print('accept not received, closing connection...')
            sock.sendto(b'END', client_address)

        while connection:
            try:
                if stop:
                    sock.sendto(b'con-res 0xFE', client_address)
                # setting available idle-time for recvfrom-function
                sock.settimeout(4.0)
                print('\nwaiting to receive message...')

                data, client_address = sock.recvfrom(4096)

                try:
                    # splits incoming message into array separated by predefined split, so that message-time, message
                    # and counter can be extracted and used separately
                    split = data.decode().split("<!split!>")
                    # checks if client's counter is either above or below server's counter
                    if int(split[2]) >= counter or int(split[2]) < int(counter)-1:
                        print('package incomplete, closing connection...')
                        sock.sendto(b'Package incomplete' + b'<!split!>' + str(counter).encode(), client_address)
                        break
                # bypasses the index error given if the message only consists of a string
                except IndexError:
                    if data.decode() == 'con-h 0x00':
                        print('client-message: ' + data.decode())
                        sock.sendto(b'con-h 0x00' + b'<!split!>' + str(counter).encode(), client_address)
                        continue
                    else:
                        print(data.decode())
                        break
                except ValueError:
                    sock.sendto(b'Package incomplete' + b'<!split!>' + str(counter).encode(), client_address)
                    break

                if split[1] == 'END':
                    print('client has closed connection')
                    break

                if split[0] == 'con-res 0xFE':
                    break
                # formats the variables above and puts them into arguments {} in the string below
                print('received {} bytes from {}'.format(len(data), client_address))
                print('message from {}:'.format(client_address), split[1])
                # sends error-message if time of message has been the same x number of times in a row, thereby
                # exceeding message-limit
                if msg_counter > conf.getint("client", "max_packages"):
                    print('package number exceeded, closing connection...')
                    sock.sendto(b'Package limit reached', client_address)
                    break

                if data:
                    # checks if the time attached to incoming message is the same as current time
                    # and increments accordingly
                    if split[0] == myTime.clock():
                        msg_counter += 1
                    else:
                        msg_counter = 0
                    sock.sendto(str('[' + myTime.clock() + ']').encode() + b'<!split!>' + b'I am a server'
                                + b'<!split!>' + str(counter).encode(), client_address)
                    counter += 2
            # throws exception if socket timeout is reached and continues loop to send stop-message to client
            except socket.timeout:
                print('socket has reached timeout')
                stop = True
                continue

    # handles exception given if program is stopped while waiting for user input
    except KeyboardInterrupt:
        print('shutting down server...')

    finally:
        sock.close()


def save_to_file(handshake):
    log = open("handshake_log.txt", "a")
    log.write(handshake)


server()
