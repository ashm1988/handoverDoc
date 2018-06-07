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
    exchange_details = {}
    headings = []
    exchadapters = []

    # Get adapter configuration headings
    for adapter_headings in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='Configuration']"):
        logging.debug("Headings: %s", adapter_headings.attrib.get('name'))
        headings.append(adapter_headings.attrib.get('name'))
    headings.insert(0, 'Adapter Name')
    headings.remove('Execution Management')
    headings.remove('Regulatory')

    # get exchange adapters
    for exchadapter in xmlroot.find(".//Item[@name='Exchange Adapters']"):
        exchadapters.append(exchadapter.attrib.get('name'))

    for adapter in exchadapters:
        for values in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
            if adapter not in exchange_details:
                exchange_details[adapter] = {}
            exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
        for sub_exchanges in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Sub-Exchanges']" % adapter):
            exchange_details[adapter]['Sub-Exchanges'].append(sub_exchanges.attrib.get('name'))
        for trader_logins in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Trader Logins']" % adapter):
            exchange_details[adapter]['Trader Logins'].append(trader_logins.attrib.get('name'))
        for connections in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']" % adapter):
            exchange_details[adapter]['Connection'].append(connections.attrib.get('value'))
        exchange_details[adapter]['Connection'].remove(None)
        exchange_details[adapter]['Sub-Exchanges'].remove(None)
        exchange_details[adapter]['Trader Logins'].remove(None)
        del exchange_details[adapter]['Regulatory']
        del exchange_details[adapter]['Execution Management']
        exchange_details[adapter]['Logging'] = [xmlroot.find(
            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get('value')]


    for idx, item in enumerate(headings):
        if item == 'Connection':
            del headings[idx]
            headings.insert(idx, "Host; Port; Target Comp; Sender Comp; Sender Sub; Username")

    print exchadapters
    print sorted(headings)
    for adapter in sorted(exchange_details.iterkeys()):
        print adapter, exchange_details[adapter]

    create_csv(headings, exchange_details)



    print headings


def create_csv(headings, exchange_details):
    logging.debug("writing csv")

    #  Create csv as hostname_instance
    f = open("test.csv", "w")


    #  If FrontTrade Add user accounts and Exchange adapters, if Price just add users
    # Add Exchange adapter info
    for heading in sorted(headings):
        f.write("%s," % heading)
    f.write("\n")
    for adapter in sorted(exchange_details):
        f.write("%s," % adapter)
        for heading in sorted(exchange_details[adapter].keys()):
            f.write("%s," % "; ".join(exchange_details[adapter][heading]))
        f.write("\n")



    logging.debug("saving csv")
    f.close()









ice_adapters(xmlroot)