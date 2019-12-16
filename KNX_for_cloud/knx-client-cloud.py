# PYTHON3 KNX-CLIENT
# Brigljevic/GONZALEZ
# 09.2019

import sys
import socket
import time
import argparse
import textwrap

import datetime
import json
import os
import ssl
import jwt
import paho.mqtt.client as mqtt

from argparse import RawTextHelpFormatter
from knxnet import *

######################################################################
## KNX DEDICATED FUNCTIONS ###########################################
## START #############################################################
######################################################################

## In the following code, "client" or "_cl" is the remote controller
## client and "gateway" or "_gt" points to the controlled device

def recv_data(sock):
    data_recv, addr = sock.recvfrom(1024)
    recv_data_object = knxnet.decode_frame(data_recv)
    return recv_data_object

def conn_req(sock, data_endpoint, control_endpoint, gateway_ip, gateway_port):
    conn_req_object = knxnet.create_frame(
        knxnet.ServiceTypeDescriptor.CONNECTION_REQUEST,
        data_endpoint, control_endpoint)
    conn_req_dtgrm = conn_req_object.frame
    sock.sendto (conn_req_dtgrm, (gateway_ip, gateway_port))

def conn_state_req(sock, channel_id, control_endpoint, gateway_ip, gateway_port):
    conn_state_req_object = knxnet.create_frame(
        knxnet.ServiceTypeDescriptor.CONNECTION_STATE_REQUEST,
        channel_id, control_endpoint)
    conn_state_req_dtgrm = conn_state_req_object.frame
    sock.sendto (conn_state_req_dtgrm, (gateway_ip, gateway_port))

def tunn_req(sock, dest_addr_group, channel_id, data, data_size, apci, gateway_ip, gateway_port):
    tunn_req_object = knxnet.create_frame(
        knxnet.ServiceTypeDescriptor.TUNNELLING_REQUEST,
        dest_addr_group, channel_id, data, data_size, apci)
    tunn_req_dtgrm = tunn_req_object.frame
    sock.sendto (tunn_req_dtgrm, (gateway_ip, gateway_port))

def tunn_ack(sock, channel_id, status, tunn_seq_count, gateway_ip, gateway_port):
    tunn_req_object = knxnet.create_frame(
        knxnet.ServiceTypeDescriptor.TUNNELLING_ACK,
        channel_id, status, tunn_seq_count)
    tunn_req_dtgrm = tunn_req_object.frame
    sock.sendto (tunn_req_dtgrm, (gateway_ip, gateway_port))

def disc_req(sock, channel_id, control_endpoint, gateway_ip, gateway_port):
    disc_req_object = knxnet.create_frame(
        knxnet.ServiceTypeDescriptor.DISCONNECT_REQUEST,
        channel_id, control_endpoint)
    disc_req_dtgrm = disc_req_object.frame
    sock.sendto (disc_req_dtgrm, (gateway_ip, gateway_port))

def KNX_rw(data_endpoint, control_endpoint, gateway_ip, gateway_port, group_address, payload):
    KNX_out = [0]
    
    # Socket creation
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('',3672))

    # Sending connection request - Step 1
    conn_req(sock, data_endpoint, control_endpoint, gateway_ip, gateway_port)
    print("\nSending connection request...")

    # Recieving connection response - Step 2
    conn_gt_resp_object = recv_data(sock)
    conn_channel_id = conn_gt_resp_object.channel_id
    print("Connection open, channel ID is : {}".format(conn_channel_id))

    # Sending connection state request - Step 3
    conn_state_req(sock, conn_channel_id, control_endpoint, gateway_ip, gateway_port)
    print("\nSending connection state request...")

    # Recieving connection state response - Step 4
    conn_gt_resp_object = recv_data(sock)
    conn_state_resp = conn_gt_resp_object.status
    if conn_state_resp == 0:
        print("Connection status is {}, continuing...".format(conn_state_resp))
    else:
        print("Connection status is {}, exiting...".format(conn_state_resp))
        KNX_out = [11]
        return KNX_out

    # Sending tunnelling request - Step 5
    dest_addr_group = knxnet.GroupAddress.from_str(group_address)
    data, data_size, apci = payload[0], payload[1], payload[2]
    tunn_req(sock, dest_addr_group, conn_channel_id, data, data_size, apci, gateway_ip, gateway_port)
    print("\nSending tunnelling request...")

    # Receiving tunnelling acknowledgment - Step 6
    tunn_gt_ack_object = recv_data(sock)
    tunn_gt_ack_status = tunn_gt_ack_object.status
    if tunn_gt_ack_status == 0:
        print("Tunnelling status is {}, continuing...".format(tunn_gt_ack_status))
    else:
        print("Tunneling status is {}, exiting...".format(tunn_gt_ack_status))
        KNX_out = [12]
        return KNX_out

    # Return of dataservice set as 0x2e (46) - Step 7
    tunn_gt_req_object = recv_data(sock)
    tunn_gt_data_service = tunn_gt_req_object.data_service
    tunn_gt_seq_count = tunn_gt_req_object.sequence_counter
    if tunn_gt_data_service == 46:
        print("\nGateway tunneling request is 0x{0:02x}, continuing...".format(tunn_gt_data_service))
    else:
        print("\nGateway tunneling request is not 0x(0:02x), exiting...".format(tunn_gt_data_service))
        KNX_out = [13]
        return KNX_out

    # Sending tunnelling acknowledgment after successful comparison - Step 8
    tunn_cl_ack_status = 0
    tunn_ack(sock, conn_channel_id, tunn_cl_ack_status, tunn_gt_seq_count, gateway_ip, gateway_port)
    print("Sending tunnelling acknowledgment with status 0.")

    # When requesting state of blinds, second return of dataservice set
    if group_address[0] == '4':
        tunn_gt_req_object = recv_data(sock)
        tunn_gt_data = tunn_gt_req_object.data
        print("\nSecond gateway tunneling request (reading the state of the blinds)")
        print("The state of the blinds is {}, continuing...".format(tunn_gt_data))
        KNX_out.append(tunn_gt_data)

    # Sending disconnect request - Step 9
    disc_req(sock, conn_channel_id, control_endpoint, gateway_ip, gateway_port)
    print("\nSending disconnect request...")

    # Receiving disconnect response - Step 10
    disc_status = recv_data(sock).status
    print("Disconnect response status is {}, disconnecting...".format(disc_status))

    # Ending and exiting the script
    print("\nProtocol steps are complete. Have a nice day :)\n")
    time.sleep(1)
    return KNX_out

######################################################################
## KNX DEDICATED FUNCTIONS ###########################################
## END ###############################################################
######################################################################

######################################################################
## MQTT DEDICATED FUNCTIONS ##########################################
## START #############################################################
######################################################################

def create_jwt(project_id, private_key_file, algorithm):
    """Create a JWT (https://jwt.io) to establish an MQTT connection."""
    token = {
        'iat': datetime.datetime.utcnow(),
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
        'aud': project_id
    }
    with open(private_key_file, 'r') as f:
        private_key = f.read()
    print('Creating JWT using {} from private key file {}'.format(
        algorithm, private_key_file))
    return jwt.encode(token, private_key, algorithm=algorithm)


def error_str(rc):
    """Convert a Paho error to a human readable string."""
    return '{}: {}'.format(rc, mqtt.error_string(rc))

######################################################################
## MQTT DEDICATED FUNCTIONS ##########################################
## END ###############################################################
######################################################################

def parse_command_line_args():
   
    parser = argparse.ArgumentParser(
        description = 'Description',
        formatter_class = RawTextHelpFormatter)
    
    parser.add_argument(
        'project_id',
        help = 'Google Cloud project name')
    
    parser.add_argument(
        'registry_id',
        help = 'Cloud IoT registry ID')

    parser.add_argument(
        'device_id',
        help = 'Cloud IoT device ID')

    parser.add_argument(
        'private_key_file',
        help = 'Path to private key file')

    parser.add_argument(
        'algorithm',
        choices = ['RS256', 'ES256'],
        help = 'Encryption algorithm to use to generate the JWT')

    parser.add_argument(
        '--cloud_region',
        default = 'eu-west1',
        help = 'Google Cloud region (default: eu-west1)')

    parser.add_argument(
        '--ca_certs',
        default = 'roots.pem',
        help = textwrap.dedent('''\
        CA root certificate (default: roots.pem)
        Get from https://pki.google.com/roots.pem'''))

    parser.add_argument(
        '--num_messages',
        type = int,
        default = 100,
        help = 'Number of message to publish (default: 100)')

    parser.add_argument(
        '--mqtt_bridge_hostname',
        default = 'mqtt.googleapis.com',
        help = 'MQTT bridge hostname (default: mqtt.googleapis.com)')

    parser.add_argument(
        '--mqtt_bridge_port',
        type = int,
        default = 8883,
        help = 'MQTT bridge port (default: 8883)')

    parser.add_argument(
        '--message_type',
        choices = ['event', 'state'],
        default = 'event',
        help = textwrap.dedent('''\
        Indicates whether the message to be published is a:
        - Telemetry event (default)
        - Device state message'''))
    
    return parser.parse_args()

class Device(object):
    def __init__(self):
        self.data_endpoint = ''
        self.control_endpoint = ''
        self.gateway_ip = ''
        self.gateway_port = ''
        self.group_address = ''
        self.payload = ''

    def update_and_return_current_position(self):
        return KNX_rw(
            self.data_endpoint,
            self.control_endpoint,
            self.gateway_ip,
            self.gateway_port,
            self.group_address,
            self.payload)

    def wait_for_connection(self, timeout):
        total_time = 0
        while not self.connected and total_time < timeout:
            time.sleep(1)
            total_time += 1
        if not self.connected:
            raise RuntimeError('Could not connect to MQTT bridge.')

    def on_connect(self, unused_client, unused_userdata, unused_flags, rc):
        print('Connection result: ', error_str(rc))
        self.connected = True

    def on_disconnect(self, unused_client, unused_userdata, rc):
        print('Disconnected: ', error_str(rc))
        self.connected = False

    def on_publish(self, unused_client, unused_userdata, unused_mid):
        print('Published message acknowledged (PUBACK received).')

    def on_subscribe(self, unused_client, unused_userdata, unused_mid, granted_qos):
        print('Subscribed: ', granted_qos)
        if granted_qos[0] = 128:
            print('Subscription failed.')

    def on_message(self, unused_client, unused_userdata, message):
        payload = message.payload.decode('utf-8')
        print('Received message \'{}\' on topic \'{}\' with QOS {}'.format(payload, message.topic, str(message.qos)))

        if not payload:
            return
        
        payload_data = json.loads(payload)
        
        knx_action = payload_data['action']
        knx_floor = payload_data['floor']
        knx_bloc = payload_data['bloc']
        knx_data = payload_data['data']
        knx_size = payload_data['size']
        knx_apci = payload_data['apci']

        group_address = knx_action + '/' + knx_floor + '/' + knx_bloc
        knx_payload = [knx_data, knx_size, knx_apci]

        endpoint_ip = '0.0.0.0'
        gateway_ip = '127.0.0.1'
        gateway_port = 3671
        endpoint_port = 3672

        data_endpoint = (endpoint_ip, endpoint_port)
        control_endpoint = (endpoint_ip, endpoint_port)

        print()
        print("Target :           {:>15}:{:>4}".format(gateway_ip, gateway_port))
        print("Data endpoint :    {:>15}:{:>4}".format(endpoint_ip, endpoint_port))
        print("Control endpoint : {:>15}:{:>4}".format(endpoint_ip, endpoint_port))
        print("Group address :    {:>20}".format(group_address))
        print("Payload :          {:>20}".format(str(knx_payload)[1:-1]))

        self.data_endpoint = data_endpoint
        self.control_endpoint = control_endpoint
        self.gateway_ip = gateway_ip
        self.gateway_port = gateway_port
        self.group_address = group_address
        self.payload = knx_payload

def main():
    
    args = parse_command_line_args()

    client = mqtt.Client(
        client_id = 'projects/{}/locations/{}/registries/{}/devices/{}'.format(
            args.project_id, args.cloud_region, args.registry_id, args.device_id))
    client.username_pw_set(
        username = 'unused',
        password = create_jwt(
            args.project_id, args.private_key_file, args.algorithm))
    client.tls_set(ca_certs = args.ca_certs, tls_version = ssl.PROTOCOL_TLSv1_2)

    device = Device()

##    dict_payload = {
##        'action' : args.action,
##        'floor' : args.floor,
##        'bloc' : args.bloc,
##        'data' : args.data,
##        'size' : args.size,
##        'apci' : args.apci
##        }

    dict_payload = {
        'action' : 4,
        'floor' : 4,
        'bloc' : 1,
        'data' : 200,
        'size' : 2,
        'apci' : 2
        }

    json_payload = json.dumps(dict_payload)

    client.on_connect = device.on_connect
    client.on_publish = device.on_publish
    client.on_disconnect = device.on_disconnect
    client.on_subscribe = device.on_subscribe
    client.on_message = device.on_message

    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)

    while True:
        mqtt_telemetry_topic = '/devices/{}/events'.format(args.device_id)
        mqtt_config_topic = '/devices/{}/config'.format(args_device_id)
        device.wait_for_connection(5)
        client.subscribe(mqtt_config_topic, qos = 1)

        KNX_out = device.update_and_return_current_position()
        KNX_err = KNX_out[0]
        KNX_data = KNX_out[1] is len(KNX_out) > 1 else 'EMPTY'

        payload = json.dumps({
            'Error code': KNX_err,
            'Data': KNX_data})
        print('Publishing payload', payload)
        client.publish(mqtt_telemetry_topic, payload, qos = 1)
        time.sleep(10)

##    client.loop_start()
##    client.disconnect()
##    client.loop_stop()
##    print('Finished loop successfully. Goodbye!')

###################################################

if __name__ == '__main__':
    main()









































    
