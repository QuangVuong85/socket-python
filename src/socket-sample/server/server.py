import socket
import os


def handler():
    if os.path.exists('/tmp/python_unix_sockets_example'):
        os.remove('/tmp/python_unix_sockets_example')

    print('Opening socket...')
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind('/tmp/python_unix_sockets_example')

    print('Listening...')
    while True:
        datagram = server.recv(1024)
        if not datagram:
            break
        else:
            print('-' * 20)
            print(datagram.decode('utf-8'))
            if 'DONE' == datagram.decode('utf-8'):
                break

    print('-' * 20)
    print('Shutting down...')
    server.close()
    os.remove('/tmp/python_unix_sockets_example')
    print('Done')


def handler_host_port():
    HOST = '127.0.0.1'
    PORT = 65432

    print('Opening socket...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        print('Listening {}...'.format((HOST, PORT)))
        s.listen()
        conn, addr = s.accept()
        with conn:
            print('Connected by', addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                else:
                    print('-' * 20)
                    print(data.decode('utf-8'))
                conn.sendall(data)

    print('-' * 20)
    print('Shutting down...')
    print('Done')


def main():
    # handler()
    handler_host_port()


if __name__ == '__main__':
    main()
