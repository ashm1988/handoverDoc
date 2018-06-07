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
# tree = ET.parse('XMLFile1.xml')
tree = ET.parse('MSGW.xml')
# tree = ET.parse('ICE.xml')
xmlroot = tree.getroot()
orderbooks = {}

# def get_orderbooks_joe(xmlroot, flatten):
#     for orderbook in xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
#         get_orderbooks_recurse_joe(orderbook.attrib.get('name'), orderbook)
#
#
# def get_orderbooks_recurse_joe(parentKey, orderbooks):
#     for child in orderbooks.find(".//Item[@name='Children']"):
#         print "Key: " + parentKey + "." + child.attrib.get('name')
#         get_orderbooks_recurse_joe(parentKey + "." + child.attrib.get('name'), child)
#
#
# def get_orderbooks(xmlroot, orderbooks):
#     for grandparent in xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
#         orderbooks[grandparent.attrib.get('name')] = [grandparent.attrib.get('name')]
#
#         for parent in grandparent.find(".//Item[@name='Children']"):
#             orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]
#             orderbooks[grandparent.attrib.get('name')].append(parent.attrib.get('name'))
#
#             for child in parent.find(".//Item[@name='Children']"):
#                 orderbooks[child.attrib.get('name')] = [child.attrib.get('name')]
#                 orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))
#                 orderbooks[grandparent.attrib.get('name')].append(child.attrib.get('name'))
#
#                 for baby in child.find(".//Item[@name='Children']"):
#                     orderbooks[baby.attrib.get('name')] = [baby.attrib.get('name')]
#                     orderbooks[child.attrib.get('name')].append(baby.attrib.get('name'))
#                     orderbooks[parent.attrib.get('name')].append(baby.attrib.get('name'))
#                     orderbooks[grandparent.attrib.get('name')].append(baby.attrib.get('name'))
#
#     return orderbooks
#
#
# def user_orderbook(xmlroot, orderbooks):
#     user_accounts = {}  # dict for the user accounts and accociated parent orderbooks
#     users_orderbooks = {}  # dict for users and all assigned (including child) orderbooks
#
#     # Collects all users and accociated parent orderbooks and adds them to the user_account dict as below example
#     #                                                           user_account = {amcfarlane: [amcfarlane, ne, etc..]
#     for users in xmlroot.find(".//Item[@name='User Management']//Item[@name='Users']"):
#         if users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
#             user_accounts[users.attrib.get('name')] = []
#             for user in users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
#                 user_accounts[users.attrib.get('name')].append(user.attrib.get('name'))
#
#     # Diffs the orderbooks assigned to the users in the user_accounts dict against the Orderbooks dict from
#     # get_orderbooks() and then adds the users with all the child orderbooks to users_orderbooks dict as below example
#     #                                  user_orderbooks = {amcfarlane: [OT, amcfarlane, fpotter, ne, ne-trader1, etc..]
#     for user, orderbook in user_accounts.items():  # find the user to get the orderbooks for
#         users_orderbooks[user] = []
#         for orderbook in user_accounts[user]:
#             for ob in orderbooks[orderbook]:
#                 print "User: %s, Orderbook: %s, Child orderbooks: %s" % (user, orderbook, ob)
#                 users_orderbooks[user].append(ob)
#
#     # print example
#     for user in users_orderbooks:
#         print user, users_orderbooks[user]
#
#
# def get_orderbooks2(xmlroot, orderbooks):
#     findstr = ".//Item[@name='Order Management']//Item[@name='Orderbooks']"
#     grandparent = xmlroot.find(findstr)
#
#     while grandparent is not None:  # while grandparent is not = to None
#         for parent in grandparent:  # for children orderbooks in Orderbooks
#             orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]  # add the orderbook as the name and the the name to itself (virroot : [virroot]
#             findstr = findstr + "//Item[@name='Children']"  # add the child node to the findstr
#             grandparent = xmlroot.find(findstr)  # update the grandparent locaton
#             for child in grandparent:  # for the children of grandparent -> parent (".//Item[@name='Order Management']//Item[@name='Orderbooks']//Item[@name='Children']"
#                 orderbooks[child.attrib.get('name')] = [child.attrib.get('name')]
#                 orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))
#
#     return orderbooks
#
#
# # def flat_ob(xmlroot, orderbooks):
# #     root_orderbook = ".//Item[@name='Order Management']//Item[@name='Orderbooks']"
# #     for root in root_orderbook
# #         orderbooks[root.attrib.get('name')] = []
#
#     #
#     # print orderbooks
#     # get_keys(xmlroot, orderbooks)
#
#
# def get_keys(xmlroot, orderbooks):
#     for parent in orderbooks.find(".//Item[@name='Children']"):
#         orderbooks[root_orderbook.attrib.get('name')].append(parent.attrib.get('name'))
#
#
#
# def printorderbooks(orderbooks):
#     for orderbook in sorted(orderbooks.iterkeys()):
#         print orderbook, ": ", orderbooks[orderbook]


def globex():
    exchadapters = []
    exchange_details = {}
    headings = []


    # Get adapter configuration headings
    for adapter_headings in xmlroot.find(".//Item[@name='Exchange Adapters']//Item[@name='Configuration']"):
        logging.debug("Headings: %s", adapter_headings.attrib.get('name'))
        headings.append(adapter_headings.attrib.get('name'))

    headings.insert(0, 'Adapter Name')


    # Get exchange adapters
    for exchadapter in xmlroot.find(".//Item[@name='Exchange Adapters']"):
        logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
        exchadapters.append(exchadapter.attrib.get('name'))

    # # Collect all the exchange session info into a dictionary called Globex
    # for adapter in exchadapters:
    #     for values in xmlroot.find(
    #             ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
    #         logging.debug("Adapter info: %s", values.attrib.get('value'))
    #         exchange_details.append(values.attrib.get('value'))

    for adapter in exchadapters:
        # Get adapters and top level details
        for values in xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
            if adapter not in exchange_details:
                exchange_details[adapter] = {}
            exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
        # Get Sub exchanges
        for sub_exchanges in xmlroot.find(
            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Sub-Exchanges']" % adapter):
            exchange_details[adapter]['Sub-Exchanges'].append(sub_exchanges.attrib.get('name'))
        # Confirm logging enabled
        exchange_details[adapter]['Logging'] = [xmlroot.find(
            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get('value')]

    for adapter in exchange_details:
        exchange_details[adapter]['Sub-Exchanges'].remove(None)

    print sorted(headings)
    for adapter in exchange_details:
        print
        print adapter,
        for heading in sorted(exchange_details[adapter].keys()):
            print ";".join(exchange_details[adapter][heading]),

    print
    for adapter in exchange_details:
        print adapter, exchange_details[adapter]


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













    # for heading in sorted(headings):
    #     print heading
    # print
    # for adapter in exchange_details:
    #     # print ";".join(exchange_details[adapter]['Sub-Exchanges'])
    #     things.append([
    #         adapter,
    #         "".join(exchange_details[adapter]['Firm ID']),
    #         "".join(exchange_details[adapter]['Logging']),
    #         "".join(exchange_details[adapter]['Market Segment Gateway']),
    #         "".join(exchange_details[adapter]['Session ID']),
    #         ";".join(exchange_details[adapter]['Sub-Exchanges']),
    #         "".join(exchange_details[adapter]['Target Address']),
    #         "".join(exchange_details[adapter]['Target Port']),
    #     ])
    #     logging.debug("%s,%s,%s,%s,%s,%s,%s,%s" % \
    #           (adapter,
    #            "".join(exchange_details[adapter]['Firm ID']),
    #            "".join(exchange_details[adapter]['Logging']),
    #            "".join(exchange_details[adapter]['Market Segment Gateway']),
    #            "".join(exchange_details[adapter]['Session ID']),
    #            ";".join(exchange_details[adapter]['Sub-Exchanges']),
    #            "".join(exchange_details[adapter]['Target Address']),
    #            "".join(exchange_details[adapter]['Target Port']),
    #            ))









def main():
    globex()


if __name__ == '__main__':
    main()
