import xml.etree.ElementTree as ET
import logging
import argparse
import socket
import sys
import re
import os
import zipfile
import os.path
import datetime

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)


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
            raise Exception("Socket failed to connect: %s" % str(err))

        # Connect to the server
        logging.debug("connecting to %s:%s", connection[3], connection[4])
        try:
            self.new_socket.connect((connection[3], int(connection[4])))
        except socket.error as err:
            raise Exception(err)

        message = \
            '<Handshake version=\"2.0\"/>' \
            '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>'

        self.new_socket.send(message)

        while 1:
            data = self.new_socket.recv(8192)
            if not re.search(r'result="error"', data):
                if re.search(r'<Login result="success"/>', data):
                    logging.info(data)
                    self.receive_data()
                    break
            else:
                raise Exception(data)

    def receive_data(self):
        total_data = []

        request = '<Request updateType=\"snapshot\" type=\"items\"></Request>'

        self.new_socket.send(request)

        while 1:
            data = self.new_socket.recv(8192)
            # logging.debug(data)
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
        # self.exchange_details, self.headings = ExchangeAdapters(self.xml, self.xmlroot).ice()
        ProcessAnalyticData.create_csv(self)
        # print self.exchange_details
        # print self.headings

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
            if users.find(".//Item[@name='Permissions']//Item[@name='Trading']//Item[@name='Orderbooks']") is not None:
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

    def pick_exchange(self):
        globex = ['ft4cme', 'ft4nym', 'ft4nymex', 'ft4cbt', 'ft4gbx']
        ice = ['ft4iceuk', 'ft4iceeu', 'ft4iceus', 'ft4icecan']
        lme = ['ft4lme']
        eurex = ['ft4eur']
        nord = ['ft4nord', 'ft4omx']
        nlx = ['ft4nlx']

        exchange = self.data['description'][2][:-1]  # ft4cme
        adapter_detail = ExchangeAdapters(self.xml, self.xmlroot, self.f)
        logging.debug("Getting %s specific data", exchange)
        if exchange in globex:
            adapter_detail.globex()
        elif exchange in ice:
            adapter_detail.ice()
        elif exchange in eurex:
            adapter_detail.eurex()
        elif exchange in lme:
            adapter_detail.lme()
        elif exchange in nord:
            adapter_detail.nord()
        else:
            logging.error("Unknown %s for adapter details display", exchange)

    def create_csv(self):
        csvname = self.data['hostname'][2] + '_' + self.data['description'][2] + ".csv"
        logging.debug("Write CSV: Writing %s", csvname)

        #  Create csv as hostname_instance
        self.f = open(csvname, "w")
        self.f.write("Hostname:,%s\n" % self.data['hostname'][2])
        self.f.write("Instance:,%s\n" % self.data["description"][2])

        #  Add server IPS
        self.f.write("Network IPs:\n")
        for network in self.networks:
            self.f.write("%s,%s\n" % (network[0], network[1]))
        self.f.write("\n")

        #  Add instance Port headings
        for lists in sorted(self.data.iterkeys(), reverse=True):
            if re.search(r'port|fix', lists):
                self.f.write(self.data[lists][0] + ",")
        self.f.write("\n")
        #  Add ports
        for lists in sorted(self.data.iterkeys(), reverse=True):
            if re.search(r'port|fix', lists):
                self.f.write(self.data[lists][2] + ",")
        self.f.write("\n")
        self.f.write("\n")

        #  If FrontTrade Add user accounts and Exchange adapters, if Price just add users
        if self.data['type'][2] == 'FrontTrade':
            # Add Exchange adapter info
            ProcessAnalyticData.pick_exchange(self)

            #  Add Users and orderbooks
            self.f.write("\n")
            self.f.write("\n")
            self.f.write("Users, Associated accounts:\n")
            for users, orderbooks in sorted(self.users_orderbooks.iteritems()):
                self.f.write("%s" % users)
                for orderbook in sorted(orderbooks):
                    self.f.write(",%s" % orderbook)
                self.f.write("\n")




        else:
            self.f.write("Users:\n")
            for user in self.users:
                self.f.write(user + "\n")

        logging.info("Saving %s", csvname)
        self.f.close()

    def zip_all(self):
        path = os.path.dirname(os.path.abspath(__file__))
        files = os.listdir(path)
        fdate = datetime.date.today().strftime("%Y%m%d")
        zf = zipfile.ZipFile(os.path.join(path, 'handoverdoc_%s.zip' % fdate), mode='w')
        for f in files:
            if f.endswith('.csv'):
                logging.info('Zipiing %s', f)
                zf.write(os.path.join(path, f), f, compress_type=zipfile.ZIP_DEFLATED)
        zf.close()

        for f in files:
            if f.endswith('.csv'):
                logging.info('deleting %s', f)
                os.remove(os.path.join(path, f))

class ExchangeAdapters(object):
    def __init__(self, xml, xmlroot, f):
        self.xml = xml
        self.xmlroot = xmlroot
        self.exchange_details = {}
        self.headings = ['Adapter Name']
        self.f = f

    def globex(self):
        exchadapters = []

        # Get exchange adapters
        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
            exchadapters.append(exchadapter.attrib.get('name'))

        for adapter in exchadapters:
            # Get adapters and top level details
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
            # Get Sub exchanges
            for sub_exchanges in self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Sub-Exchanges']" % adapter):
                self.exchange_details[adapter]['Sub-Exchanges'].append(sub_exchanges.attrib.get('name'))
            self.exchange_details[adapter]['Sub-Exchanges'].remove(None)
            # Confirm logging enabled
            self.exchange_details[adapter]['Logging'] = [self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get('value')]

        ExchangeAdapters.get_headings(self)
        ExchangeAdapters.write_csv(self)

    def ice(self):
        exchadapters = []

        # get exchange adapters
        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            exchadapters.append(exchadapter.attrib.get('name'))

        for adapter in exchadapters:
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
            for sub_exchanges in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Sub-Exchanges']" % adapter):
                self.exchange_details[adapter]['Sub-Exchanges'].append(sub_exchanges.attrib.get('name'))
            for trader_logins in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Trader Logins']" % adapter):
                self.exchange_details[adapter]['Trader Logins'].append(trader_logins.attrib.get('name'))
            for connections in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']" % adapter):
                self.exchange_details[adapter][connections.attrib.get('name')] = [connections.attrib.get('value')]
            self.exchange_details[adapter]['Logging'] = [self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get(
                'value')]
            del self.exchange_details[adapter]['Regulatory']
            del self.exchange_details[adapter]['Execution Management']
            del self.exchange_details[adapter]['Connection']

        ExchangeAdapters.get_headings(self)
        ExchangeAdapters.write_csv(self)

    def eurex(self):
        exchadapters = []

        # Get exchange adapters
        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
            exchadapters.append(exchadapter.attrib.get('name'))
        logging.debug("Adapters: %s", exchadapters)

        for adapter in exchadapters:
            # Get adapters and top level details
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
                for gateway in self.xmlroot.find(
                        ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']" % adapter):
                    self.exchange_details[adapter][gateway.attrib.get('name')] = [gateway.attrib.get('value')]
                    for con_detail in self.xmlroot.find(
                            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']//Item[@name='%s']" % (
                            adapter, gateway.attrib.get('name'))):
                        self.exchange_details[adapter][gateway.attrib.get('name')].append(con_detail.attrib.get('value'))
                    for trader in self.xmlroot.find(
                            ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']//Item[@name='Trader Logins']" % adapter):
                        self.exchange_details[adapter]['Trader Logins'] = [trader.attrib.get('name')]
            self.exchange_details[adapter]['Logging'] = [self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get(
                'value')]
            del self.exchange_details[adapter]['Execution Management']
            del self.exchange_details[adapter]['Connection']
            del self.exchange_details[adapter]['Exchange Throttle']
            del self.exchange_details[adapter]['Regulatory']

        ExchangeAdapters.get_headings(self)
        ExchangeAdapters.write_csv(self)

    def lme(self):
        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
            self.exchadapters.append(exchadapter.attrib.get('name'))
        logging.debug("Adapters: %s", self.exchadapters)

        for adapter in self.exchadapters:
            # Get adapters and top level details
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
            self.exchange_details[adapter]['Logging'] = [self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get(
                'value')]

        ExchangeAdapters.get_headings(self)
        ExchangeAdapters.write_csv(self)

    def nord(self):
        exchadapters = []

        for exchadapter in self.xmlroot.find(".//Item[@name='Exchange Adapters']"):
            logging.debug("Adapters: %s", exchadapter.attrib.get('name'))
            self.exchadapters.append(exchadapter.attrib.get('name'))
        logging.debug("Adapters: %s", self.exchadapters)
        
        for adapter in exchadapters:
            for values in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']" % adapter):
                if adapter not in self.exchange_details:
                    self.exchange_details[adapter] = {}
                self.exchange_details[adapter][values.attrib.get('name')] = [values.attrib.get('value')]
            for connections in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Connection']" % adapter):
                self.exchange_details[adapter][connections.attrib.get('name')] = [connections.attrib.get('value')]
            for sub_exchange in self.xmlroot.find(
                    ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Sub-Exchanges']" % adapter):
                self.exchange_details[adapter]['Sub-Exchanges'].append(sub_exchange.attrib.get('name'))
            self.exchange_details[adapter]['Logging'] = [self.xmlroot.find(
                ".//Item[@name='Exchange Adapters']//Item[@name='%s']//Item[@name='Configuration']//Item[@name='Logging']//Item[@name='Enabled']" % adapter).attrib.get(
                'value')]
            del self.exchange_details[adapter]['Application ID']
            del self.exchange_details[adapter]['Dedicated Trades']
            del self.exchange_details[adapter]['Broker']
            del self.exchange_details[adapter]['Broker Orders']
            del self.exchange_details[adapter]['Synthetic Order Update']
            del self.exchange_details[adapter]['Connection']

    def get_headings(self):
        for adapter in self.exchange_details:
            for heading, li in self.exchange_details[adapter].viewitems():
                self.headings.append(heading)
        self.headings = list(set(self.headings))

    def write_csv(self):
        # Remove 'None Values'
        for adapter in self.exchange_details:
            for value in self.exchange_details[adapter]:
                for val in self.exchange_details[adapter][value]:
                    if val is None:
                        self.exchange_details[adapter][value].remove(None)

        for heading in sorted(self.headings):
            self.f.write("%s," % heading)
        self.f.write("\n")
        for adapter in self.exchange_details:
            self.f.write("%s," % adapter)
            for heading in sorted(self.exchange_details[adapter].keys()):
                self.f.write("%s," % ";".join(self.exchange_details[adapter][heading]))
            self.f.write("\n")


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
        try:
            connection.connect_socket(conn)
        # connection.receive_data()
            connection.common_info(analytics_port)
        # connection.pick_exchange()
        except Exception as err:
            logging.error("%s", err)

    connection.zip_all()
    logging.info('Complete')


if __name__ == '__main__':
    main()
