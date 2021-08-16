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


def refresh_ipc(ipc):
    peers = ['Functionator', 'Communicator']
    checked = -1
    while len(peers) != checked:
        print(f'[{int(time.time()-STIME)}] Checking IPC {peers}')
        checked = 0
        for peer in peers:
            if peer in ipc.keys():
                try:
                    ipc[peer].sendall(b'HELLO')
                    data = ipc[peer].recv(4096)
                    if data != b'HELLO':
                        raise socket.timeout
                    else:
                        checked = checked + 1
                except socket.timeout:
                    ipc.pop(peer)
            if peer not in ipc.keys():
                connect = (CONFIG[peer]['BindAddress'], int(CONFIG[peer]['BindPort']))
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect(connect)
                except ConnectionRefusedError:
                    continue
                if DEBUG:
                    print(f'Process {os.getpid()} connect to {connect}')
                ipc[peer] = sock
        time.sleep(1)

    return ipc


def main():
    if DEBUG:
        print(f'Parsed arguments {FLAGS}')
        print(f'Unparsed arguments {_}')

    CONFIG.read(FLAGS.config)

    # Create server socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # reuse
    bind = (CONFIG['Controller']['BindAddress'], int(CONFIG['Controller']['BindPort']))
    if DEBUG:
        print(f'Process {os.getpid()} bind to {bind}')
    sock.bind(bind)
    sock.listen()
    sock.setblocking(0)

    sock_list = [sock]

    ipc = dict()
    ipc = refresh_ipc(ipc)

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

