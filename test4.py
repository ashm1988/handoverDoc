import xml.etree.ElementTree as ET
import logging
import argparse
import socket
import sys
import re
import os.path

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)


class CreateSocket():
    def __init__(self):
        pass

    def connect_socket(self, connection):
        """ Creates a socket connection, connects to the connections in the dictionary and sends log on request """
        # try and make a socket connection
        try:
            self.new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.debug('socket created')
        except socket.error as err:
            logging.error('socket connection: ' + str(err))
            raise Exception("Socket failed to connect: %s" % str(err))

        # Connect to the server
        logging.debug("connecting to %s:%s", connection[3], connection[4])
        try:
            self.new_socket.connect((connection[3], int(connection[4])))
        except socket.error as err:
            logging.error(err)
            sys.exit()

        message = \
            '<Handshake version=\"2.0\"/>' \
            '<Login username=\"admin\" passphrase=\"admin\" encryptMethod=\"none\"/>'

        self.new_socket.send(message)

        while 1:
            data = self.new_socket.recv(8192)
            if not re.search(r'result="error"', data):
                if re.search(r'<Login result="success"/>', data):
                    logging.info(data)
                    self.receive_data()
                    break
            else:
                raise Exception(data)

    def receive_data(self):
        total_data = []

        request = '<Request updateType=\"snapshot\" type=\"items\"></Request>'

        self.new_socket.send(request)

        while 1:
            data = self.new_socket.recv(8192)
            logging.debug(data)
            if not re.search(r'result="error"', data):
                if not re.search(r"</Response>", data):
                    total_data.append(data)
                else:
                    total_data.append(data)
                    break
            else:
                total_data.append(data)
                logging.error(total_data)
                sys.exit()

        self.new_socket.close()
        logging.debug('Connection to analytics successful and data received')
        self.xml = ''.join(total_data)
        # logging.debug("Received data: "+self.xml)
        self.xmlroot = ET.fromstring(self.xml)


def main():
    connection = [
        'blank',
        'blank',
        'blank',
        '172.18.165.86',
        12001
    ]

    socket = CreateSocket()
    socket.connect_socket(connection)
    # socket.receive_data()

if __name__ == '__main__':
    main()
