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
# tree = ET.parse('ICE.xml')
# tree = ET.parse('MSGW.xml')
tree = ET.parse('Eurex.xml')
xmlroot = tree.getroot()
orderbooks = {}

def eurex():
    exchadapters = []
    exchange_details = {}
    headings = ['Adapter Name']

    # Get exchange adapters
    for exchadapter in xmlroot.find(".//Item[@name='Exchange Adapters']"):
        logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
        exchadapters.append(exchadapter.attrib.get('name'))
    logging.debug("Adapters: %s", exchadapters)

    for adapter in exchadapters:
        # Get adapters and top level details
        for values in xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
            if adapter not in exchange_details:
                exchange_details[adapter] = {}
            exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
            for gateway in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']" % adapter):
                exchange_details[adapter][gateway.attrib.get('name')] = [gateway.attrib.get('value')]
                for con_detail in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']//Item[@name='%s']" % (adapter, gateway.attrib.get('name'))):
                    exchange_details[adapter][gateway.attrib.get('name')].append(con_detail.attrib.get('value'))
                for trader in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']//Item[@name='Trader Logins']" % adapter):
                    exchange_details[adapter]['Trader Logins'] = [trader.attrib.get('name')]
        exchange_details[adapter]['Logging'] = [xmlroot.find(
            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get('value')]
        del exchange_details[adapter]['Execution Management']
        del exchange_details[adapter]['Connection']
        del exchange_details[adapter]['Exchange Throttle']
        del exchange_details[adapter]['Regulatory']
    # Remove 'None Values'
    for adapter in exchange_details:
        for value in exchange_details[adapter]:
            for val in exchange_details[adapter][value]:
                if val is None:
                    exchange_details[adapter][value].remove(None)

    for adapter in exchange_details:
        for heading, list3 in exchange_details[adapter].viewitems():
            headings.append(heading)
    headings = list(set(headings))


    f = open("test.csv", "w")

    #  If FrontTrade Add user accounts and Exchange adapters, if Price just add users
    # Add Exchange adapter info
    for heading in sorted(headings):
        f.write("%s," % heading)
    f.write("\n")
    for adapter in exchange_details:
        f.write("%s," % adapter)
        for heading in sorted(exchange_details[adapter].keys()):
            f.write("%s," % ";".join(exchange_details[adapter][heading]))
        f.write("\n")

    f.close()



















def main():
    eurex()


if __name__ == '__main__':
    main()
