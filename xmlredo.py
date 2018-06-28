import xml.etree.ElementTree as ET
import logging
import argparse
import socket
import sys
import re
import os.path
# from HandoverDoc import XMLProcess
import HandoverDoc

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
# tree = ET.parse('XMLFile1.xml')
# tree = ET.parse('ICE.xml')
# tree = ET.parse('MSGW.xml')
# self.xmlroot = tree.getroot()
# FRVersion = "FR4"
XMLProcess = HandoverDoc.XMLProcess


class CreateSocket(XMLProcess):
    def __init__(self, conn_file, category):
        XMLProcess.__init__(self, conn_file, category)

    def connect_socket(self, connection):
        """ Creates a socket connection, connects to the connections in the dictionary and sends log on request """
        # try and make a socket connection
        try:
            self.new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.debug('socket created')
        except socket.error as err:
            logging.error('socket connection: ' + str(err))
            sys.exit()

        # Connect to the server
        logging.debug("connecting to %s:%s", connection[3], connection[4])
        try:
            self.new_socket.connect((connection[3], int(connection[4])))
        except socket.error as err:
            logging.error(err)
            sys.exit()

        login = \
            '<Handshake version=\"2.0\"/>' \
            '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>'
            # '<Request updateType=\"snapshot\" type=\"items\"></Request>'

        # Send log on message
        try:
            self.new_socket.send(login)
            logging.debug('sending handshake, login and requests')
        except socket.error as err:
            logging.error('send failed: %s', err)
            sys.exit()

    #     loginrequest = self.new_socket.recv(8192)
    #     if not re.search(r'result="error"', loginrequest):
    #         print 'no error'
    #         request = '<Request updateType=\"snapshot\" type=\"items\"></Request>'
    #         try:
    #             self.new_socket.send(request)
    #             logging.debug('sending handshake, login and requests')
    #         except socket.error:
    #             logging.error('send failed')
    #             sys.exit()
    #
    # # def receive_data(self):
        total_data = []

        while 1:
            data = self.new_socket.recv(8192)
            # logging.debug(data)
            self.new_socket.
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
    #
    #     self.new_socket.shutdown(socket.SHUT_RDWR)
    #     self.new_socket.close()
    #     logging.debug('Connection to analytics successful and data received')
    #     # del total_data[:2]
    #     self.xml = ''.join(total_data)
    #     # logging.debug("Received data: "+self.xml)
    #     # self.xmlroot = ET.fromstring(self.xml)


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--category", default="TestBed", choices=["Production", "TestBed", "BuildOut"],
                        help="Server Category i.e. Production, TestBed (default: %(default)s")
    parser.add_argument("-f", "--connection_file", default="Connections.xml", help="Path to Connections.xml")
    args = parser.parse_args()

    # Create instance of connection
    connection = CreateSocket(args.connection_file, args.category)
    ports = connection.get_ports()
    for conn in ports.values():
        analytics_port = conn[4]
        # try:
        connection.connect_socket(conn)
        connection.receive_data()



if __name__ == '__main__':
    main()
