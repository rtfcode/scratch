#!/usr/bin/python

from blockext import *
import socket
import select
import urllib
import base64

class SSocket:
    def __init__(self):
        self.sockets = {}

    def _on_reset(self):
        print 'reset!!!'
        for key in self.sockets.keys():
            if self.sockets[key]['socket']:
                self.sockets[key]['socket'].close()
        self.sockets = {}

    def add_socket(self, type, proto, sock, host, port):
        if self.is_connected(sock) or self.is_listening(sock):
            print 'add_socket: socket already in use'
            return
        self.sockets[sock] = {'type': type, 'proto': proto, 'host': host, 'port': port, 'reading': 0, 'closed': 0}

    def set_socket(self, sock, s):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'set_socket: socket doesn\'t exist'
            return
        self.sockets[sock]['socket'] = s

    def set_control(self, sock, c):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'set_control: socket doesn\'t exist'
            return
        self.sockets[sock]['control'] = c

    def set_addr(self, sock, a):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'set_addr: socket doesn\'t exist'
            return
        self.sockets[sock]['addr'] = a


    def create_socket(self, proto, sock, host, port):
        if self.is_connected(sock) or self.is_listening(sock):
            print 'create_socket: socket already in use'
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        self.add_socket('socket', proto, sock, host, port)
        self.set_socket(sock, s)


    def create_listener(self, proto, sock, ip, port):
        if self.is_connected(sock) or self.is_listening(sock):
            print 'create_listener: socket already in use'
            return
        s = socket.socket()
        s.bind((ip, port))
        s.listen(5)
        self.add_socket('listener', proto, sock, ip, port)
        self.set_control(sock, s)


    def accept_connection(self, sock):
        if not self.is_listening(sock):
            print 'accept_connection: socket is not listening'
            return
        s = self.sockets[sock]['control']
        c, addr = s.accept()
        self.set_socket(sock, c)
        self.set_addr(sock, addr)


    def close_socket(self, sock):
        if self.is_connected(sock) or self.is_listening(sock):
            self.sockets[sock]['socket'].close()
            del self.sockets[sock]


    def is_connected(self, sock):
        if sock in self.sockets:
            if self.sockets[sock]['type'] == 'socket' and not self.sockets[sock]['closed']:
                return True
        return False


    def is_listening(self, sock):
        if sock in self.sockets:
            if self.sockets[sock]['type'] == 'listener':
                return True
        return False


    def write_socket(self, data, type, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'write_socket: socket doesn\'t exist'
            return
        if not 'socket' in self.sockets[sock] or self.sockets[sock]['closed']:
            print 'write_socket: socket fd doesn\'t exist'
            return
        buf = ''
        if type == "raw":
            buf = data
        elif type == "c enc":
            buf = data.decode('string_escape')
        elif type == "url enc":
            buf = urllib.unquote(data)
        elif type == "base64":
            buf = base64.b64decode(data)

        totalsent = 0
        while totalsent < len(buf):
            sent = self.sockets[sock]['socket'].send(buf[totalsent:])
            if sent == 0:
                self.sockets[sock]['closed'] = 1
                return
            totalsent += sent


    def clear_read_flag(self, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'readline_socket: socket doesn\'t exist'
            return
        if not 'socket' in self.sockets[sock]:
            print 'readline_socket: socket fd doesn\'t exist'
            return
        self.sockets[sock]['reading'] = 0


    def reading(self, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            return 0
        if not 'reading' in self.sockets[sock]:
            return 0
        return self.sockets[sock]['reading']


    def readline_socket(self, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'readline_socket: socket doesn\'t exist'
            return
        if not 'socket' in self.sockets[sock] or self.sockets[sock]['closed']:
            print 'readline_socket: socket fd doesn\'t exist'
            return
        self.sockets[sock]['reading'] = 1
        str = ''
        c = ''
        while c != '\n':
            read_sockets, write_sockets, error_sockets = select.select([self.sockets[sock]['socket']] , [], [], 0.1)
            if read_sockets:
                c = self.sockets[sock]['socket'].recv(1)
                str += c
                if c == '':
                    self.sockets[sock]['closed'] = 1
                    c = '\n' # end the while loop
            else:
                c = '\n' # end the while loop with empty or partially received string
        self.sockets[sock]['readbuf'] = str
        if str:
            self.sockets[sock]['reading'] = 2
        else:
            self.sockets[sock]['reading'] = 0


    def recv_socket(self, length, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            print 'recv_socket: socket doesn\'t exist'
            return
        if not 'socket' in self.sockets[sock] or self.sockets[sock]['closed']:
            print 'recv_socket: socket fd doesn\'t exist'
            return
        self.sockets[sock]['reading'] = 1
        read_sockets, write_sockets, error_sockets = select.select([self.sockets[sock]['socket']] , [], [], 0.1)
        if read_sockets:
            str = self.sockets[sock]['socket'].recv(length)
            if str == '':
                self.sockets[sock]['closed'] = 1
        else:
            str = ''

        self.sockets[sock]['readbuf'] = str
        if str:
            self.sockets[sock]['reading'] = 2
        else:
            self.sockets[sock]['reading'] = 0



    def n_read(self, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            return 0
        if self.sockets[sock]['reading'] == 2:
            return len(self.sockets[sock]['readbuf'])
        else:
            return 0


    def readbuf(self, type, sock):
        if not self.is_connected(sock) and not self.is_listening(sock):
            return ''
        if self.sockets[sock]['reading'] == 2:
            data = self.sockets[sock]['readbuf']
            buf = ''
            if type == "raw":
                buf = data
            elif type == "c enc":
                buf = data.encode('string_escape')
            elif type == "url enc":
                buf = urllib.quote(data)
            elif type == "base64":
                buf = base64.b64encode(data)
            return buf

        else:
            return ''


descriptor = Descriptor(
    name = "Scratch Sockets",
    port = 5000,
    blocks = [
        Block('create_socket', 'command', 'create %m.proto conx %m.sockno host %s port %n',
            defaults=["tcp", 1, "127.0.0.1", 0]),
        Block('create_listener', 'command', 'create %m.proto listener %m.sockno ip %s port %n',
            defaults=["tcp", 1, "0.0.0.0", 0]),
        Block('accept_connection', 'command', 'accept connection %m.sockno',
            defaults=[1]),
        Block('close_socket', 'command', 'close socket %m.sockno',
            defaults=[1]),
        Block('is_connected', 'predicate', 'socket %m.sockno connected?'),
        Block('is_listening', 'predicate', 'socket %m.sockno listening?'),
        Block('write_socket', 'command', 'write %s as %m.encoding to socket %m.sockno',
            defaults=["hello", "raw", 1]),
        Block('readline_socket', 'command', 'read line from socket %m.sockno',
            defaults=[1]),
        Block('recv_socket', 'command', 'read %n bytes from socket %m.sockno',
            defaults=[255, 1]),
        Block('n_read', 'reporter', 'n_read from socket %m.sockno',
            defaults=[1]),
        Block('readbuf', 'reporter', 'received buf as %m.encoding from socket %m.sockno',
            defaults=["raw", 1]),
        Block('reading', 'reporter', 'read flag for socket %m.sockno',
            defaults=[1]),
        Block('clear_read_flag', 'command', 'clear read flag for socket %m.sockno',
            defaults=[1]),
    ],
    menus = dict(
        proto = ["tcp", "udp"],
        encoding = ["raw", "c enc", "url enc", "base64"],
        sockno = [1, 2, 3, 4, 5],
    ),
)

extension = Extension(SSocket, descriptor)

if __name__ == '__main__':
    extension.run_forever(debug=True)


