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
orderbooks = {}

def get_orderbooks_joe(xmlroot, flatten):
    for orderbook in xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
        get_orderbooks_recurse_joe(orderbook.attrib.get('name'), orderbook)

def get_orderbooks_recurse_joe(parentKey, orderbooks):
    for child in orderbooks.find(".//Item[@name='Children']"):
        print "Key: " + parentKey + "." + child.attrib.get('name')
        get_orderbooks_recurse_joe(parentKey + "." + child.attrib.get('name'), child)


def get_orderbooks(xmlroot, orderbooks):
    for grandparent in xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
        orderbooks[grandparent.attrib.get('name')] = [grandparent.attrib.get('name')]

        for parent in grandparent.find(".//Item[@name='Children']"):
            orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]
            orderbooks[grandparent.attrib.get('name')].append(parent.attrib.get('name'))

            for child in parent.find(".//Item[@name='Children']"):
                orderbooks[child.attrib.get('name')] = [child.attrib.get('name')]
                orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))
                orderbooks[grandparent.attrib.get('name')].append(child.attrib.get('name'))

                for baby in child.find(".//Item[@name='Children']"):
                    orderbooks[baby.attrib.get('name')] = [baby.attrib.get('name')]
                    orderbooks[child.attrib.get('name')].append(baby.attrib.get('name'))
                    orderbooks[parent.attrib.get('name')].append(baby.attrib.get('name'))
                    orderbooks[grandparent.attrib.get('name')].append(baby.attrib.get('name'))

    return orderbooks


def user_orderbook(xmlroot, orderbooks):
    user_accounts = {}  # dict for the user accounts and accociated parent orderbooks
    users_orderbooks = {}  # dict for users and all assigned (including child) orderbooks

    # Collects all users and accociated parent orderbooks and adds them to the user_account dict as below example
    #                                                           user_account = {amcfarlane: [amcfarlane, ne, etc..]
    for users in xmlroot.find(".//Item[@name='User Management']//Item[@name='Users']"):
        if users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
            user_accounts[users.attrib.get('name')] = []
            for user in users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
                user_accounts[users.attrib.get('name')].append(user.attrib.get('name'))

    # Diffs the orderbooks assigned to the users in the user_accounts dict against the Orderbooks dict from
    # get_orderbooks() and then adds the users with all the child orderbooks to users_orderbooks dict as below example
    #                                  user_orderbooks = {amcfarlane: [OT, amcfarlane, fpotter, ne, ne-trader1, etc..]
    for user, orderbook in user_accounts.items():  # find the user to get the orderbooks for
        users_orderbooks[user] = []
        for orderbook in user_accounts[user]:
            for ob in orderbooks[orderbook]:
                print "User: %s, Orderbook: %s, Child orderbooks: %s" % (user, orderbook, ob)
                users_orderbooks[user].append(ob)

    # print example
    for user in users_orderbooks:
        print user, users_orderbooks[user]


def get_orderbooks2(xmlroot, orderbooks):
    findstr = ".//Item[@name='Order Management']//Item[@name='Orderbooks']"
    grandparent = xmlroot.find(findstr)

    while grandparent is not None:  # while grandparent is not = to None
        for parent in grandparent:  # for children orderbooks in Orderbooks
            orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]  # add the orderbook as the name and the the name to itself (virroot : [virroot]
            findstr = findstr + "//Item[@name='Children']"  # add the child node to the findstr
            grandparent = xmlroot.find(findstr)  # update the grandparent locaton
            for child in grandparent:  # for the children of grandparent -> parent (".//Item[@name='Order Management']//Item[@name='Orderbooks']//Item[@name='Children']"
                orderbooks[child.attrib.get('name')] = [child.attrib.get('name')]
                orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))

    return orderbooks


# def flat_ob(xmlroot, orderbooks):
#     root_orderbook = ".//Item[@name='Order Management']//Item[@name='Orderbooks']"
#     for root in root_orderbook
#         orderbooks[root.attrib.get('name')] = []

    #
    # print orderbooks
    # get_keys(xmlroot, orderbooks)


def get_keys(xmlroot, orderbooks):
    for parent in orderbooks.find(".//Item[@name='Children']"):
        orderbooks[root_orderbook.attrib.get('name')].append(parent.attrib.get('name'))



def printorderbooks(orderbooks):
    for orderbook in sorted(orderbooks.iterkeys()):
        print orderbook, ": ", orderbooks[orderbook]


def main():
    flat_orderbooks = get_orderbooks(xmlroot, orderbooks)
    # get_orderbooks_joe(xmlroot)
    #flat_orderbooks = flat_ob(xmlroot, orderbooks)
    printorderbooks(flat_orderbooks)
    user_orderbook(xmlroot, flat_orderbooks)


if __name__ == '__main__':
    main()
