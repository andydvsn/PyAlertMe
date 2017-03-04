import sys
import time
import logging
sys.path.insert(0, '../')

from classes import *
import unittest
from mock_serial import Serial

class TestHub(unittest.TestCase):

    def setUp(self):
        self.serialObj = Serial()
        self.hubObj = Hub(self.serialObj)

    def tearDown(self):
        self.hubObj.halt()

    def test_receive_message(self):
        self.maxDiff = None

        message = {
            'cluster':          b'\x00\xf6',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\xc2\x16',
            'rf_data':          b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.hubObj.receive_message(message)
        result = self.hubObj.list_nodes()
        expected = [{
            'messagesReceived': 1,
            'associated': True,
            'addrLong': '\x00\ro\x00\x03\xbb\xb9\xf8',
            'addrShort': '\x88\x9f',
            'name': 'Unknown Device',
            'createdOn': int(time.time()),
            'messagesSent': 0,
            'id': '00:0d:6f:00:03:bb:b9:f8',
            'lastSeen': int(time.time()),
            'attributes': {
                'hwVersion': {
                    'reportReceivedTime': int(time.time()),
                    'reportedValue': 20045
                },
                'manufactuerDate': {
                    'reportReceivedTime': int(time.time()),
                    'reportedValue': '2013-09-26'
                },
                'manufacturer': {
                    'reportReceivedTime': int(time.time()),
                    'reportedValue': 'AlertMe.com'
                },
                'model': {
                    'reportReceivedTime': int(time.time()),
                    'reportedValue': 'SmartPlug'
                }
            }
        }]
        self.assertEqual(result, expected)

    def test_endpoint_request(self):
        message = {
            'cluster':          b'\x00\x06',
            'dest_endpoint':    b'\x02',
            'id':               'rx_explicit',
            'options':          b'\x01',
            'profile':          b'\x00\x00',
            'rf_data':          b'',
            'source_addr':      b'\x88\x9f',
            'source_addr_long': b'\x00\ro\x00\x03\xbb\xb9\xf8',
            'src_endpoint':     b'\x02'
        }
        self.hubObj.receive_message(message)
        result = self.serialObj.get_data_written()
        expected = b'~\x00\x19\x11\x00\x00\ro\x00\x03\xbb\xb9\xf8\x88\x9f\x00\x02\x00\xf0\xc2\x16\x00\x00\x19\x01\xfa\x00\x01\xfd'
        self.assertEqual(result, expected)


    def test_parse_tamper_state(self):
        result = Hub.parse_tamper_state(b'\t\x00\x00\x02\xe8\xa6\x00\x00')
        expected = 1
        self.assertEqual(result, expected, "Tamper Detected")

        result = Hub.parse_tamper(b'\t\x00\x01\x01+\xab\x00\x00')
        expected = 0
        self.assertEqual(result, expected, "Tamper OK")

    def test_parse_power_consumption(self):
        result = Hub.parse_power_factor(b'\t\x00\x81%\x00')
        expected = {'instantaneousPower': 37}
        self.assertEqual(result, expected)

    def test_parse_power_consumption(self):
        result = Hub.parse_power_consumption(b'\t\x00\x82Z\xbb\x04\x00\xdf\x86\x04\x00\x00')
        expected = {
            'powerConsumption': 310106,
            'upTime': 296671
        }
        self.assertEqual(result, expected)

    def test_parse_switch_state(self):
        result = Hub.parse_switch_state(b'\th\x80\x07\x01')
        expected = {'state' : 'ON'}
        self.assertEqual(result, expected)

        result = Hub.parse_switch_state(b'\th\x80\x06\x00')
        expected = {'state' : 'OFF'}
        self.assertEqual(result, expected)

    def test_parse_version_info(self):
        serialObj2 = Serial()
        deviceObj = SmartPlug(serialObj2)

        message = deviceObj.get_type()
        result = Hub.parse_version_info(message['data'])
        expected = {
            'Version': 20045,
            'Manufacturer': 'AlertMe.com',
            'Type': 'SmartPlug',
            'ManufactureDate': '2013-09-26'
        }
        self.assertEqual(result, expected)
        deviceObj.halt()

        result = Hub.parse_version_info(b'\tq\xfeMN\xf8\xb9\xbb\x03\x00o\r\x009\x10\x07\x00\x00)\x00\x01\x0bAlertMe.com\tSmartPlug\n2013-09-26')
        expected = {
            'Version': 20045,
            'Manufacturer': 'AlertMe.com',
            'Type': 'SmartPlug',
            'ManufactureDate': '2013-09-26'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfebI\xb2\x8a\xc2\x00\x00o\r\x009\x10\r\x00\x03#\x01\x01\x0bAlertMe.com\x0bPower Clamp\n2010-05-19')
        expected = {
            'Version': 18786,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Power Clamp',
            'ManufactureDate': '2010-05-19'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe+\xe8\xc0ax\x00\x00o\r\x009\x10\x01\x00\x01#\x00\x01\x0bAlertMe.com\rButton Device\n2010-11-15')
        expected = {
            'Version': 59435,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Button Device',
            'ManufactureDate': '2010-11-15'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe\xb6\xb7x\x1dx\x00\x00o\r\x009\x10\x06\x00\x00#\x00\x02\x0bAlertMe.com\nPIR Device\n2010-11-24')
        expected = {
            'Version': 47030,
            'Manufacturer': 'AlertMe.com',
            'Type': 'PIR Device',
            'ManufactureDate': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\t\x00\xfe\xad\xe3jj\x1b\x00\x00o\r\x009\x10\x05\x00\x06\x12\x00\x01\x0bAlertMe.com\x12Door/Window sensor\n2008-04-17')
        expected = {
            'Version': 58285,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Door/Window sensor',
            'ManufactureDate': '2008-04-17'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\tp\xfe\x82@\xc1e\x1d\x00\x00o\r\x009\x10\x04\x00\x01#\x00\x01\x0bAlertMe.com\x0eAlarm Detector\n2010-11-24')
        expected = {
            'Version': 16514,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Alarm Detector',
            'ManufactureDate': '2010-11-24'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\t0\xfe3B\x08BI\x00\x00o\r\x009\x10\x03\x00\x03#\x00\x01\x0bAlertMe.com\rKeyfob Device\n2010-11-10')
        expected = {
            'Version': 16947,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Keyfob Device',
            'ManufactureDate': '2010-11-10'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\t\x00\xfe\x1b\x15V_\x1b\x00\x00o\r\x009\x10\x02\x00\x07\x12\x00\x02\x0bAlertMe.com\x06Beacon\n2008-07-08')
        expected = {
            'Version': 5403,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Beacon',
            'ManufactureDate': '2008-07-08'
        }
        self.assertEqual(result, expected)

        result = Hub.parse_version_info(b'\t\x00\xfe\xde\xa4\xeav\x1b\x00\x00o\r\x009\x10\x02\x00\x06\x12\x01\x01\x0bAlertMe.com\x04Lamp\n2008-04-17')
        expected = {
            'Version': 42206,
            'Manufacturer': 'AlertMe.com',
            'Type': 'Lamp',
            'ManufactureDate': '2008-04-17'
        }
        self.assertEqual(result, expected)

    def test_parse_range_info(self):
        result = Hub.parse_range_info(b'\t+\xfd\xc5w')
        expected = {'RSSI' : 197}
        self.assertEqual(result, expected)

    def test_parse_button_press(self):
        result = Hub.parse_button_press(b'\t\x00\x00\x00\x02\xbf\xc3\x00\x00')
        expected = {'counter': 50111, 'state': 'OFF'}
        self.assertEqual(result, expected, "State 0, Conter 50111")

        result = Hub.parse_button_press(b'\t\x00\x01\x00\x01\x12\xca\x00\x00')
        expected = {'counter': 51730, 'state': 'ON'}
        self.assertEqual(result, expected, "State 1, Conter 51730")

    def test_parse_status_update(self):
        result = Hub.parse_status_update(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'Temp_F': 87.008, 'Type': 'Key Fob', 'Counter': 13019}
        self.assertEqual(result, expected)

    def test_parse_security_state(self):
        result = Hub.parse_security_state(b'\t\x89\xfb\x1d\xdb2\x00\x00\xf0\x0bna\xd3\xff\x03\x00')
        expected = {'ReedSwitch': 'open', 'TamperSwith': 'closed'}
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main(verbosity=2)
