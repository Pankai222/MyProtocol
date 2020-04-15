import socket

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 43098)
print('Connecting to server...\n')

client_ip = socket.gethostbyname(socket.gethostname())

# variable for incrementing message and response-number
counter = 0

try:
    connected = True
    print('Client Com-{}: '.format(counter) + client_ip + ' sending connection request')
    sock.sendto(client_ip.encode(), server_address)
    accept, server = sock.recvfrom(4096)
    print('Server Com-{}: '.format(counter) + accept.decode())

    # split accept-message and set connected to false if first index is not 'accept'
    split = accept.decode().split()
    if split[0] != 'accept':
        connected = False

    else:
        print('Client Com-{}: accept'.format(counter))

    # indefinite while-loop that runs until client sends 'bye'
    while connected:
        # waits for user-input then encodes it to bytes for datagram
        print('\nYour message: ', end='')
        message = input().encode() + b'#' + str(counter).encode()
        msg_split = message.decode().split("#")
        print('Client Message-{}: '.format(counter) + msg_split[0])
        counter += 2

        # Send data
        sent = sock.sendto(message, server_address)

        # if input contains END, close socket
        if msg_split[0] == 'END':
            break

        # Receive response. If response breaks counter, close socket
        data, server = sock.recvfrom(4096)
        data_split = data.decode().split("#")

        if data_split[0] == 'Package incomplete':
            break

        print('Server Response-{}: {!r}'.format(data_split[1], data_split[0]))

finally:
    print('Closing connection...')
    sock.close()
