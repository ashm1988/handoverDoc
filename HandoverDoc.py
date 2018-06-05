import xml.etree.ElementTree as ET
import logging
import argparse
import socket
import sys
import re
import os.path

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
# tree = ET.parse('XMLFile1.xml')
# tree = ET.parse('ICE.xml')
# tree = ET.parse('MSGW.xml')
# self.xmlroot = tree.getroot()
# FRVersion = "FR4"


class XMLProcess(object):
    def __init__(self, conn_file, category):
        self.conn_file = conn_file
        self.connections = {}
        self.category = category
        self.FRVersion = "FR4"

    def get_ports(self):
        """ Gets the connection details from the Conn Mon XML"""
        logging.debug('Creating connection dictionary from Connections.xml')
        confile = ET.parse(self.conn_file)
        root = confile.getroot()

        # Creates a dictionary of connections
        for ConnectionConfiguration in root.findall('ConnectionConfiguration'):
            if ConnectionConfiguration.find("FRVersion").text == self.FRVersion and \
               ConnectionConfiguration.find("Category").text == self.category and \
               ConnectionConfiguration.find("Enabled").text == "true":
                self.connections[ConnectionConfiguration.find("Name").text] = \
                    ConnectionConfiguration.find("Category").text, \
                    ConnectionConfiguration.find("Type").text, \
                    ConnectionConfiguration.find("FRVersion").text, \
                    ConnectionConfiguration.find("Address").text, \
                    ConnectionConfiguration.find("AnalyticsPort").text, \
                    ConnectionConfiguration.find("Username").text, \
                    ConnectionConfiguration.find("Password").text

        # log all connections
        for server in self.connections:
            if self.connections[server][0] == self.category and self.connections[server][2] == self.FRVersion:
                logging.debug('Connections: %s %s', server, self.connections[server])

        # Count connections and log
        if len(self.connections) > 0:
            logging.info('Number of connections: %s', len(self.connections))
        else:
            logging.error('No connection details')

        return self.connections


class CreateSocket(XMLProcess):
    def __init__(self, conn_file, category):
        XMLProcess.__init__(self, conn_file, category)

    def connect_socket(self, connection):
        """ Creates a socket connection, connects to the connections in the dictionary and sends log on request """
        # try and make a socket connection
        try:
            self.new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            logging.debug('socket created')
        except socket.error as err:
            logging.error('socket connection: ' + str(err))
            sys.exit()

        # Connect to the server
        logging.debug("connecting to %s:%s", connection[3], connection[4])
        try:
            self.new_socket.connect((connection[3], int(connection[4])))
        except socket.error as err:
            logging.error(err)
            sys.exit()

        message = \
            '<Handshake version=\"2.0\"/>' \
            '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>' \
            '<Request updateType=\"snapshot\" type=\"items\"></Request>'

        # Send log on message
        try:
            self.new_socket.send(message)
            logging.debug('sending handshake, login and requests')
        except socket.error:
            logging.error('send failed')
            sys.exit()

        print (self.new_socket)

    def receive_data(self):
        total_data = []

        while 1:
            data = self.new_socket.recv(8192)
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

        self.new_socket.close()
        logging.debug('Connection to analytics successful and data received')
        del total_data[:2]
        self.xml = ''.join(total_data)
        # logging.debug("Received data: "+self.xml)
        self.xmlroot = ET.fromstring(self.xml)


class ProcessAnalyticData(CreateSocket):
    def __init__(self, conn_file, category):
        CreateSocket.__init__(self, conn_file, category)

    def common_info(self, analytics_port):
        network_names = []
        network_ips = []
        # self.users = {}
        self.analytics_port = analytics_port

        # Build common data dictionary
        self.data = {
            "type": ["Server Type", ".//Item[@name='Identity']//Item[@name='Label']"],
            "core": ["Core Version", ".//Item[@name='Identity']/Item[@name='Version']"],
            "product": ["Product", ".//Item[@name='Identity']/Item[@name='Description']"],
            "hostname": ["Hostname", ".//Item[@name='Hostname']"],
            "description": ["Description", ".//Item[@name='Name']"],
            "frapiport": ["Frapi Port", ".//Item[@name='FRAPI2']//Item[@name='Listener Port']"],
        }

        # Get Network IPs
        for network in self.xmlroot.findall(".//Item[@name='Network']/Item[@name]/Item[@name='Description']"):
            network_names.append(network.attrib.get('value'))
        for network in self.xmlroot.findall(".//Item[@name='Network']/Item[@name]/Item[@name='IPs']"):
            network_ips.append(network.attrib.get('value'))
        self.networks = (zip(network_names, network_ips))
        for network in self.networks:
            logging.debug(network)

        # Get users
        self.users = []
        for users in self.xmlroot.find(".//Item[@name='User Management']//Item[@name='Users']"):
            # if users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
            self.users.append(users.attrib.get('name'))

        if self.xmlroot.find(".//Item[@name='Identity']//Item[@name='Label']").attrib.get('value') == 'FrontTrade':
            logging.debug('Common Info: Passing to FrontTrade')
            ProcessAnalyticData.fronttrade(self)
        else:
            logging.debug('Common Info: Passing to FrontPrice')
            ProcessAnalyticData.frontprice(self)

    def fronttrade(self):
        fix_acceptors = []

        # Build dictionary
        self.data["riskport"] = ["Risk Port", ".//Item[@name='Risk Management']//Item[@name='Listener Port']"]

        # Add fix acceptors to the dictionary
        for fix_acceptor in self.xmlroot.find(".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']"):
            fix_acceptors.append(fix_acceptor.attrib.get('name'))
        logging.debug("Available fix acceptors %s", fix_acceptors)

        for acceptor in fix_acceptors:
            self.data["%s" % acceptor.lower()] = ["%s Port" % acceptor,
                                             ".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']//Item[@name='%s']//Item[@name='Listener Port']" % (
                                             acceptor)]

        ProcessAnalyticData.combine_users_and_orderbooks(self)
        ProcessAnalyticData.update_dictionary(self)
        self.exchange_details, self.headings = ExchangeAdapters(self.xml, self.xmlroot).globex()
        ProcessAnalyticData.create_csv(self)

    def frontprice(self):
        if self.xmlroot.find(".//Item[@name='Client Adapters']//Item[@name='FIX42']//Item[@name='Listener Port']") is not None:
            self.data["fix42"] = ["Fix42 Port", ".//Item[@name='Client Adapters']//Item[@name='FIX42']//Item[@name='Listener Port']"]

        ProcessAnalyticData.update_dictionary(self)
        ProcessAnalyticData.create_csv(self)

    def get_orderbooks(self):
        """ Get orderbook list """
        self.orderbooks = {}
        for grandparent in self.xmlroot.find(".//Item[@name='Order Management']//Item[@name='Orderbooks']"):
            self.orderbooks[grandparent.attrib.get('name')] = [grandparent.attrib.get('name')]

            for parent in grandparent.find(".//Item[@name='Children']"):
                self.orderbooks[parent.attrib.get('name')] = [parent.attrib.get('name')]
                self.orderbooks[grandparent.attrib.get('name')].append(parent.attrib.get('name'))

                for child in parent.find(".//Item[@name='Children']"):
                    self.orderbooks[child.attrib.get('name')] = [child.attrib.get('name')]
                    self.orderbooks[parent.attrib.get('name')].append(child.attrib.get('name'))
                    self.orderbooks[grandparent.attrib.get('name')].append(child.attrib.get('name'))

                    for baby in child.find(".//Item[@name='Children']"):
                        self.orderbooks[baby.attrib.get('name')] = [baby.attrib.get('name')]
                        self.orderbooks[child.attrib.get('name')].append(baby.attrib.get('name'))
                        self.orderbooks[parent.attrib.get('name')].append(baby.attrib.get('name'))
                        self.orderbooks[grandparent.attrib.get('name')].append(baby.attrib.get('name'))

    def combine_users_and_orderbooks(self):
        ProcessAnalyticData.get_orderbooks(self)
        user_accounts = {}  # dict for the user accounts and accociated parent orderbooks
        self.users_orderbooks = {}  # dict for users and all assigned (including child) orderbooks

        # Collects all users and accociated parent orderbooks and adds them to the user_account dict as below example
        #                                                           user_account = {amcfarlane: [amcfarlane, ne, etc..]
        for users in self.xmlroot.find(".//Item[@name='User Management']//Item[@name='Users']"):
            if users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
                user_accounts[users.attrib.get('name')] = []
                for user in users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']"):
                    user_accounts[users.attrib.get('name')].append(user.attrib.get('name'))

        # Diffs the orderbooks assigned to the users in the user_accounts dict against the Orderbooks dict from
        # get_orderbooks() and then adds the users with all the child orderbooks to users_orderbooks dict as below
        # example user_orderbooks = {amcfarlane: [OT, amcfarlane, fpotter, ne, ne-trader1, etc..]
        for user, orderbook in user_accounts.items():  # find the user to get the orderbooks for
            self.users_orderbooks[user] = []
            for orderbook in user_accounts[user]:
                for ob in self.orderbooks[orderbook]:
                    self.users_orderbooks[user].append(ob)

        # print example
        for user in self.users_orderbooks:
            logging.debug("User Orderbooks: %s %s", user, self.users_orderbooks[user])

    def update_dictionary(self):
        # Add values to dictionary
        for instance in self.data:
            logging.debug("Getting %s", instance)
            self.data[instance].append(self.xmlroot.find(self.data[instance][1]).attrib.get('value'))
        #  Add analytics port
        self.data['analyticsport'] = ['Analytics Port', '', self.analytics_port]
        for dicts in self.data:
            logging.debug("%s: %s", dicts, self.data[dicts])

    def create_csv(self):
        logging.debug("writing csv")

        #  Create csv as hostname_instance
        f = open(self.data["hostname"][2] + "_" + self.data["description"][2] + ".csv", "w")
        f.write("Hostname:,%s\n" % self.data['hostname'][2])
        f.write("Instance:,%s\n" % self.data["description"][2])

        #  Add server IPS
        f.write("Network IPs:\n")
        for network in self.networks:
            f.write("%s,%s\n" % (network[0], network[1]))
        f.write("\n")

        #  Add instance Port headings
        for lists in sorted(self.data.iterkeys(), reverse=True):
            if re.search(r'port|fix', lists):
                f.write(self.data[lists][0] + ",")
        f.write("\n")
        #  Add ports
        for lists in sorted(self.data.iterkeys(), reverse=True):
            if re.search(r'port|fix', lists):
                f.write(self.data[lists][2] + ",")
        f.write("\n")
        f.write("\n")

        #  If FrontTrade Add user accounts and Exchange adapters, if Price just add users
        if self.data['type'][2] == 'FrontTrade':
            # Add Exchange adapter info
            for heading in self.headings:
                f.write("%s," % heading)


            #  Add Users and orderbooks
            f.write("Users, Associated accounts:\n")
            for users, orderbooks in sorted(self.users_orderbooks.iteritems()):
                f.write("%s" % users)
                for orderbook in sorted(orderbooks):
                    f.write(",%s" % orderbook)
                f.write("\n")




        else:
            f.write("Users:\n")
            for user in self.users:
                f.write(user + "\n")

        logging.debug("saving csv")
        f.close()


class ExchangeAdapters(object):
    def __init__(self, xml, xmlroot):
        self.xml = xml
        self.xmlroot = xmlroot

    def globex(self):
        exchadapters = []
        self.exchange_details = {}
        self.headings = []

        # Get exchange adapters
        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            exchadapters.append(exchadapter.attrib.get('name'))

        # Collect all the exchange session info into a dictionary called Globex
        for adapter in exchadapters:
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = values.attrib.get('value')

        for dicts in self.exchange_details:
            logging.debug("%s: %s", dicts, self.exchange_details[dicts].items())



        # for dicts in exchadapters:
        #     for key in exchadapters[dicts]:
        #         if key not in self.headings:
        #             self.headings.append(key)
        #
        # print self.headings

        return self.exchange_details, self.headings



















def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--category", default="TestBed", choices=["Production", "TestBed", "BuildOut"],
                        help="Server Category i.e. Production, TestBed (default: %(default)s")
    parser.add_argument("-f", "--connection_file", default="Connections.xml", help="Path to Connections.xml")
    args = parser.parse_args()

    # Create instance of connection
    connection = ProcessAnalyticData(args.connection_file, args.category)
    ports = connection.get_ports()
    for conn in ports.values():
        analytics_port = conn[4]
        # try:
        connection.connect_socket(conn)
        connection.receive_data()
        connection.common_info(analytics_port)
        # except:
        #     pass


if __name__ == '__main__':
    main()
