import xml.etree.ElementTree as ET
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
# tree = ET.parse('XMLFile1.xml')
tree = ET.parse('ICE.xml')
# tree = ET.parse('MSGW.xml')
xmlroot = tree.getroot()


def ice_adapters(xmlroot):
    ice = {}
    exchadapters = []

    # get exchange adapters
    for exchadapter in xmlroot.find(".//Item[@name='Exchange Adapters']"):
        exchadapters.append(exchadapter.attrib.get('name'))

    # Collect all adapter info
    for adapter in exchadapters:
        if adapter not in ice:
            ice[adapter] = {}
        for config in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
            # ice[adapter].append(config.attrib.get('name'))
            for values in config:
                ice[adapter][values.attrib.get('name')] = values.attrib.get('value')
                # print adapter, config.attrib.get('name'), values.attrib.get('name'), values.attrib.get('value')

    for dicts in ice:
        logging.debug("%s: %s", dicts, ice[dicts].items())

ice_adapters(xmlroot)