import socket
import os


def handler():
    print('Connecting...')
    if os.path.exists('/tmp/python_unix_sockets_example'):
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect('/tmp/python_unix_sockets_example')
        print('Ready.')
        print('Ctrl-C to quit.')
        print('Sending \'DONE\' shuts down the server and quits.')

        while True:
            try:
                x = input('>')
                if '' != x:
                    print('Send : ', x)
                    client.send(x.encode('utf-8'))
                    if 'DONE' == x:
                        print('Shutting down.')
                        break
            except KeyboardInterrupt as key:
                print('Shutting down.')
                client.close()
                break
    else:
        print('Couldn\'t connect!')
        print('Done')


def handler_host_port():
    HOST = '127.0.0.1'
    PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        while True:
            try:
                msg = input('->')
                if '' != msg:
                    print('Send : ', msg)
                    client.sendall(bytes(msg, "utf8"))
            except KeyboardInterrupt as key:
                print('Shutting down.')
                client.close()
                break


def main():
    # handler()
    handler_host_port()


if __name__ == '__main__':
    main()
