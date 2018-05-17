import xml.etree.ElementTree as ET
import mysql.connector
import argparse
import datetime
import logging
import socket
import sys
import re
import functions

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)

connection_details = {
    'username': 'amcfarlane',
    'password': 'amcfarlane',
    'host': '172.28.101.10',
    'port': 40001,
}


def main():
    app = functions.HandoverDoc()

    app.receive_data(connection_details)




if __name__ == '__main__':
    main()
