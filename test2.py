#
# Orderbooks = {
#     "amcfarlane": ["ashfix", "ashfix1", "ashfrapi", "amcfarlane"],
#     "ashfix": ["ashfix", "ashfix1"],
#     "ashfrapi": ["ashfrapi"],
# }


import xml.etree.ElementTree as ET
import mysql.connector
import argparse
import datetime
import logging
import socket
import sys
import re
import os.path
from openpyxl import Workbook


# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
tree = ET.parse('XMLFile1.xml')
# tree = ET.parse('MSGW.xml')
xmlroot = tree.getroot()

def get_orderbooks(xmlroot):
    orderbooks = {}
    for grandparent in xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
        orderbooks[grandparent.attrib.get('name')] = [grandparent.attrib.get('name')]
        for parent in grandparent.find(".//Item[@name='Children']"):
            orderbooks[grandparent.attrib.get('name')].append(parent.attrib.get('name'))
            orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]
            for child in parent.find(".//Item[@name='Children']"):
                orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))
                orderbooks[grandparent.attrib.get('name')].append(child.attrib.get('name'))

    for orderbook in orderbooks:
        print orderbook, ": ", orderbooks[orderbook]


def main():
    get_orderbooks(xmlroot)


if __name__ == '__main__':
    main()
