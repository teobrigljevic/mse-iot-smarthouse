# PYTHON3 KNX-CLIENT
# Brigljevic/GONZALEZ
# 09.2019

import sys
import socket
import time
import argparse
import textwrap
import json

from argparse import RawTextHelpFormatter
from knxnet import *

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
        sys.exit()

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
        sys.exit()

    # Return of dataservice set as 0x2e (46) - Step 7
    tunn_gt_req_object = recv_data(sock)
    tunn_gt_data_service = tunn_gt_req_object.data_service
    tunn_gt_seq_count = tunn_gt_req_object.sequence_counter
    if tunn_gt_data_service == 46:
        print("\nGateway tunneling request is 0x{0:02x}, continuing...".format(tunn_gt_data_service))
    else:
        print("\nGateway tunneling request is not 0x(0:02x), exiting...".format(tunn_gt_data_service))
        sys.exit()

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

    # Sending disconnect request - Step 9
    disc_req(sock, conn_channel_id, control_endpoint, gateway_ip, gateway_port)
    print("\nSending disconnect request...")

    # Receiving disconnect response - Step 10
    disc_status = recv_data(sock).status
    print("Disconnect response status is {}, disconnecting...".format(disc_status))

    # Ending and exiting the script
    print("\nProtocol steps are complete. Have a nice day :)\n")
    time.sleep(1)

def parse_command_line_args():
    
    parser = argparse.ArgumentParser(
        description = 'Monitoring and controlling script for KNX-linked devices (radiators, blinds).',
        epilog = 'For simulations, use \'<ACTION> 4 1 <DATA> <SIZE> 2\' or \'<ACTION> 4 2 <DATA> <SIZE> 2\'\n'+
        'For the real devices, use \'<ACTION> 4 8 <DATA> <SIZE> 2\' or \'<ACTION> 4 9 <DATA> <SIZE> 2\'\n'+
        '(<DATA> is either {0,1} or [0,255], with respective <SIZE> 1 or 2)',
        formatter_class = RawTextHelpFormatter)
    
    parser.add_argument(
        'action',
        type = int,
        choices = [0,1,3,4],
        help = textwrap.dedent('''\
        Type of command (action) sent to the actuator:
           0: Control of the radiator\'s valves (payload: 0 to 255)
           1: Control of the blinds (payload: 0 (open) or 1 (closed))
           2: Not available
           3: Control of the blinds (payload: 0 (open) to 255 (closed))
           4: Read state of the blinds (answer: 0 (open) to 255 (closed))'''))
    
    parser.add_argument(
        'floor',
        type = int,
        help = 'Floor where the targeted device is located')

    parser.add_argument(
        'bloc',
        type = int,
        help = 'Bloc to which the device belongs')

    parser.add_argument(
        'data',
        type = int,
        help = 'Data payload ({0,1} or [0,255])')

    parser.add_argument(
        'size',
        type = int,
        help = 'Data size (1 or 2)')

    parser.add_argument(
        'apci',
        type = int,
        help = 'Data APCI (always 2)')

    parser.add_argument(
        '--mode',
        default = 'sim',
        choices = ['sim', 'prod'],
        required = False,
        help = 'Running on simulator (\'sim\', default) or on real devices (\'prod\')')

    return parser.parse_args()

def main():
    
    args = parse_command_line_args()

    dict_payload = {
        'action' : args.action,
        'floor' : args.floor,
        'bloc' : args.bloc,
        'data' : args.data,
        'size' : args.size,
        'apci' : args.apci
        }

    json_payload = json.dumps(dict_payload)

    print(json_payload)
    
    payload_data = json.loads(json_payload)

    print(payload_data)
    
    knx_action = payload_data['action']
    knx_floor = payload_data['floor']
    knx_bloc = payload_data['bloc']
    knx_data = payload_data['data']
    knx_size = payload_data['size']
    knx_apci = payload_data['apci']

    group_address = str(knx_action) + '/' + str(knx_floor) + '/' + str(knx_bloc)
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

    KNX_rw(data_endpoint, control_endpoint, gateway_ip, gateway_port, group_address, knx_payload)

###################################################

if __name__ == '__main__':
    main()
