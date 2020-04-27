import socket

# Create a UDP socket
# First argument specifies address family, second specifies socket type (in this case datagram)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind the socket to the port
server_address = ('localhost', 43098)
print('Starting up on {} port {}'.format(*server_address))
sock.bind(server_address)

connection = True


def server():
    stop = False
    counter = 1
    try:
        request, client_address = sock.recvfrom(4096)
        if request.decode() == socket.gethostbyname(socket.gethostname()):
            sock.sendto(b'accept ' + request, client_address)
            print('accept ' + request.decode())

        while connection:
            try:
                if stop:
                    sock.sendto(b'con-res 0xFE', client_address)
                # setting available idle-time for recvfrom-function
                sock.settimeout(4.0)
                print('\nWaiting to receive message...')

                data, client_address = sock.recvfrom(25)

                # splitting message from client into list, then checking if index 1 is above server's counter
                try:
                    split = data.decode().split("#")
                    if int(split[1]) > counter:
                        print('Package incomplete, closing connection...')
                        sock.sendto(b'Package incomplete' + b'#' + str(counter).encode(), client_address)
                        break

                except IndexError:
                    if data.decode() == 'con-h 0x00':
                        sock.sendto(b'con-h 0x00' + b'#' + str(counter).encode(), client_address)
                        continue
                    else:
                        print(data.decode())
                        break

                if split[0] == 'END':
                    print('Client has closed connection')
                    break

                if split[0] == 'con-res 0xFE':
                    break
                # Formats the variables above and puts them into arguments {} in the string below
                print('received {} bytes from {}'.format(len(data), client_address))
                print('Message from {}:'.format(client_address), split[0])

                if data:
                    sock.sendto(b'I am a server' + b'#' + str(counter).encode(), client_address)
                    counter += 2

            except socket.timeout:
                print('Socket has reached timeout')
                stop = True
                continue

    # Handles exception given if program is stopped while waiting for user input
    except KeyboardInterrupt:
        print('Shutting down server...')

    finally:
        sock.close()


server()
