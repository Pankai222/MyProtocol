import socket

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = ('localhost', 43098)
print('Connecting to server...\n')

# variable for incrementing message and response-number
counter = 0

try:
    start = False
    client_ip = socket.gethostbyname(socket.gethostname())
    print('Client Com-{}: '.format(counter) + client_ip + ' sending connection request')
    sock.sendto(client_ip.encode(), server_address)
    accept, server = sock.recvfrom(4096)
    print('Server Com-{}: '.format(counter) + accept.decode())

    split = accept.decode().split()
    if split[0] == 'accept':
        print('Client Com-{}: accept'.format(counter))
        start = True

    # indefinite while-loop that runs until client sends 'bye'
    while start:
        # waits for user-input then encodes it to bytes for datagram
        print('\nYour message: ', end='')
        message = input().encode() + b'#' + str(counter).encode()
        msg_split = message.decode().split("#")
        print('Client Message-{}: '.format(counter) + msg_split[0])
        counter += 2

        # Send data
        sent = sock.sendto(message, server_address)

        # Receive response
        data, server = sock.recvfrom(4096)
        data_split = data.decode().split("#")
        print('Server Response-{}: {!r}'.format(data_split[1], data_split[0]))

        if msg_split[0] == 'END':
            break

        elif data_split[0] == 'Package incomplete':
            break

finally:
    print('Closing connection...')
    sock.close()
