import xml.etree.ElementTree as ET
import logging
import socket
import sys
import re
import os.path

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='xml.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
# tree = ET.parse('XMLFile1.xml')
tree = ET.parse('ICE.xml')
# tree = ET.parse('MSGW.xml')
xmlroot = tree.getroot()