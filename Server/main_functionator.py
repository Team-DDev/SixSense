import os
import time
import configparser
import socket
import select

import cv2

FLAGS = _ = None
DEBUG = False
STIME = time.time()
CONFIG = configparser.ConfigParser()


def main():
    if DEBUG:
        print(f'Parsed arguments {FLAGS}')
        print(f'Unparsed arguments {_}')

    CONFIG.read(FLAGS.config)

    # Create server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse
    bind = (CONFIG['Functionator']['BindAddress'], int(CONFIG['Functionator']['BindPort']))
    if DEBUG:
        print(f'Process {os.getpid()} bind to {bind}')
    sock.bind(bind)
    sock.listen()
    sock.setblocking(0)

    sock_list = [sock]
    if DEBUG:
       print(f'[{int(time.time()-STIME)}] Start server')
    while True:
        try:
            read_sock, write_sock, err_sock = select.select(sock_list, sock_list, sock_list)
            # For read data from sockets
            for rsock in read_sock:
                # New connection
                if rsock == sock:
                    csock, caddr = rsock.accept()
                    if DEBUG:
                        print(f'[{int(time.time()-STIME)}] Connected with {caddr}')
                    csock.setblocking(0)
                    sock_list.append(csock)
                else:
                    csock = rsock
                    cdata = csock.recv(4096)
                    if DEBUG:
                        print(f'[{int(time.time()-STIME)}] Received {cdata} from {csock.getpeername()}')
                    if cdata == b'':
                        print(f'[{int(time.time()-STIME)}] Closing {csock.getpeername()}')
                        sock_list.remove(csock)
                        csock.close()
                        continue
                    csock.sendall(cdata)
                    print(f'[{int(time.time()-STIME)}] Sended {cdata} to {csock.getpeername()}')
            if DEBUG:
                for esock in err_sock:
                    print(f'Error {esock}')
        except KeyboardInterrupt:
            if DEBUG:
                print(f'[{int(time.time()-STIME)}] End server')
                break


if __name__ == '__main__':
    root_path = os.path.abspath(__file__)
    root_dir = os.path.dirname(root_path)
    os.chdir(root_dir)

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true',
                        help='The present debug message')
    parser.add_argument('--config', type=str, default='master.ini',
                        help='The path for configuration file')

    FLAGS, _ = parser.parse_known_args()

    FLAGS.config = os.path.abspath(os.path.expanduser(FLAGS.config))

    DEBUG = FLAGS.debug

    main()

