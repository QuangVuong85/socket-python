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


def main():
    handler()


if __name__ == '__main__':
    main()
