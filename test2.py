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


logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
# tree = ET.parse('MSGW.xml')
tree = ET.parse('MSGW.xml')
xmlroot = tree.getroot()
network_names = []
network_IPs = []

# # Get Network IPs
# for networks in xmlroot.find(".//Item[@name='Network']"):
#     for network in networks.findall(".//Item[@name='IPs']"):
#         network_ips.append(network.attrib.get('value'))
#
# for networks in xmlroot.find(".//Item[@name='Network']"):
#     for network in networks.findall(".//Item[@name]"):
#         print network.attrib.get('name'), ": ", network.attrib.get('value')


for network in xmlroot.findall(".//Item[@name='Network']/Item[@name]/Item[@name='Description']"):
   network_names.append(network.attrib.get('value'))
for network in xmlroot.findall(".//Item[@name='Network']/Item[@name]/Item[@name='IPs']"):
   network_IPs.append(network.attrib.get('value'))

networks = (zip(network_names, network_IPs))



print networks