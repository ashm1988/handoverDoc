import xml.etree.ElementTree as ET
import mysql.connector
import argparse
import datetime
import logging
import socket
import sys
import re

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
connection_details = {
    'username': 'amcfarlane',
    'password': 'amcfarlane',
    'host': '172.28.101.10',
    'port': 40001,
}


def connect_socket(conn_details):
    """ Creates a socket connection, connects to the connections in the dictionary and sends log on request """
    # try and make a socket connection
    try:
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug('socket created')
    except socket.error as err:
        logging.error('socket connection: ' + str(err))
        sys.exit()

    # Connect to the server
    logging.debug("connecting to %s", conn_details['host'])
    try:
        new_socket.connect((conn_details['host'], conn_details['port']))
    except socket.error as err:
        logging.error(err)
        sys.exit()

    message = \
        '<Handshake version=\"2.0\"/>' \
        '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>' \
        '<Request updateType=\"snapshot\" type=\"items\"></Request>'

    # Send log on message
    try:
        new_socket.send(message)
        logging.debug('sending handshake, login and requests')
    except socket.error:
        logging.error('send failed')
        sys.exit()

    return new_socket


def receive_data(the_socket):
    total_data = []

    while 1:
        data = the_socket.recv(8192)
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

    the_socket.close()
    logging.debug('Connection to analytics successful and data received')
    del total_data[:2]
    # total_data.remove(total_data[0])
    # total_data.remove(total_data[0])
    xml = ''.join(total_data)
    logging.debug("Received data: "+xml)
    return xml


def process_date(received_data):
    """ Not working """
    network_ips = []
    xmlroot = ET.fromstring(received_data)

    # Get Network IPs
    for networks in xmlroot.find(".//Item[@name='Network']"):
        for network in networks.findall(".//Item[@name='IPs']"):
            network_ips.append(network.attrib.get('value'))
    logging.debug(network_ips)

    # Get Hostname
    hostname = xmlroot.find(".//Item[@name='Hostname']").attrib.get('value')
    logging.debug(hostname)




def main():
    socket = connect_socket(connection_details)
    xml = receive_data(socket)
    process_date(xml)



if __name__ == '__main__':
    main()

