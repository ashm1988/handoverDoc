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
# tree = ET.parse('MSGW.xml')
tree = ET.parse('MSGW.xml')
xmlroot = tree.getroot()

def analytics_info(xmlroot):
    network_ips = {}
    fix_acceptors = []

    # Build dictionary
    data = {
        "core": ["Core Version", ".//Item[@name='Identity']/Item[@name='Version']"],
        "product": ["Product", ".//Item[@name='Identity']/Item[@name='Description']"],
        "hostname": ["Hostname", ".//Item[@name='Hostname']"],
        "description": ["Description", ".//Item[@name='Name']"],
        "riskport": ["Risk Port", ".//Item[@name='Risk Management']//Item[@name='Listener Port']"],
        "frapiport": ["Frapi Port", ".//Item[@name='FRAPI2']//Item[@name='Listener Port']"],
    }

    # Add fix acceptors to the dictionary
    for fix_acceptor in xmlroot.find(".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']"):
        fix_acceptors.append(fix_acceptor.attrib.get('name'))
    logging.debug(fix_acceptors)

    for acceptor in fix_acceptors:
        data["%s" % acceptor.lower()] = ["%s Port" % acceptor, ".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']//Item[@name='%s']//Item[@name='Listener Port']" % (acceptor)]

    # # Get Network IPs
    # for networks in xmlroot.find(".//Item[@name='Network']"):
    #     for network in networks.findall(".//Item[@name='IPs']"):
    #         network_ips.append(network.attrib.get('value'))

    for networks in xmlroot.find(".//Item[@name='Network']"):
        for network in networks.findall(".//Item[@name]"):
            print network.attrib.get('name'), ": ", network.attrib.get('value')

    # Add values to dictionary
    for instance in data:
        logging.debug("Getting %s", instance)
        data[instance].append(xmlroot.find(data[instance][1]).attrib.get('value'))

    # If Globex run the below (currently just running as a test)
    # globex(xmlroot)

    # logging.debug(data)

    for dicts in data:
        logging.debug("%s: %s", dicts, data[dicts])

    logging.debug("network IPs: %s", network_ips)

    return data, network_ips


def globex(xmlroot):
    exchadapters = []
    globex = {}

    # Get exchange adapters
    for exchadapter in xmlroot.find(".//Item[@name='Exchange Adapters']"):
        exchadapters.append(exchadapter.attrib.get('name'))

    # Collect all the exchange seesion info into a dictionary called Globex
    for adapter in exchadapters:
        for values in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
            if not adapter in globex:
                globex[adapter] = {}
            globex[adapter][values.attrib.get('name')] = values.attrib.get('value')

    for dicts in globex:
        logging.debug("%s: %s", dicts, globex[dicts].items())

    return globex


def excel_workbook(data, exehadapter):
    data, network_ips = data
    wb = Workbook()
    sheet = wb.active
    sheet.title = network_ips[1] + "_" + data["description"][2]
    headings = ['test', 'test2', 'test3']

    for heading in sheet.iter_rows(min_row=1):
        sheet.append(headings)



    wb.save('Handover Doc.xlsx')


def main():
    data = analytics_info(xmlroot)
    exchadapter = globex(xmlroot)
    excel_workbook(data, exchadapter)

if __name__ == '__main__':
    main()

