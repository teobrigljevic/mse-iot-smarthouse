# PYTHON3 ZWAVE-CLIENT
# Brigljevic/GONZALEZ
# 09.2019


import argparse
import datetime
import json
import os
import ssl
import time
import logging
import sys, os
import resource

import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption

import jwt
import paho.mqtt.client as mqtt

'''Initial parameters'''
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('openzwave')

######################################################################
## DEFAULT CONFIGURATION FOR MQTT ####################################
######################################################################
project_id = 'smarthouseiot-261017'
registry_id = 'smarthouse'
device_id = 'serverZWAVE'
topic = 'room02z'
private_key_file = 'rsa_private.pem'
algorithm = 'RS256'
cloud_region = 'europe-west1'

######################################################################
## DEFAULT CONFIGURATION FOR ZWAVE ###################################
######################################################################
device = "/dev/ttyACM0"
Multisensor_node = -1
Lamp_node = -1

log = "Debug"
#Define some manager options
options = ZWaveOption(device, \
  config_path="/home/pi/.local/lib/python3.7/site-packages/python_openzwave/ozw_config/config", \
  user_path=".", cmd_line="")
options.set_log_file("OZW_Log.log")
options.set_append_log_file(False)
options.set_console_output(False)
options.set_save_log_level(log)
#options.set_save_log_level('Info')
options.set_logging(False)
options.lock()
network = ZWaveNetwork(options, log=None)



######################################################################
## FUNCTIONS FOR ZWAVE ###############################################
######################################################################    
def start_network ():   
    time_started = 0
    print("------------------------------------------------------------")
    print("Waiting for network awaked : ")
    print("------------------------------------------------------------")
    for i in range(0,300):
        if network.state>=network.STATE_AWAKED:
    
            #print(" done")
            #print("Memory use : {} Mo".format( (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)))
            break
        else:
            sys.stdout.write(".")
            sys.stdout.flush()
            time_started += 1
            time.sleep(1.0)
    if network.state<network.STATE_AWAKED:
        print(".")
        print("Network is not awake but continue anyway")
    print("------------------------------------------------------------")
    print("Use openzwave library : {}".format(network.controller.ozw_library_version))
    print("Use python library : {}".format(network.controller.python_library_version))
    print("Use ZWave library : {}".format(network.controller.library_description))
    print("Network home id : {}".format(network.home_id_str))
    print("Controller node id : {}".format(network.controller.node.node_id))
    print("Controller node version : {}".format(network.controller.node.version))
    print("Nodes in network : {}".format(network.nodes_count))
    print("------------------------------------------------------------")
    print("Waiting for network ready : ")
    print("------------------------------------------------------------")
    for i in range(0,300):
        if network.state>=network.STATE_READY:
            #print(" done in {} seconds".format(time_started))
            break
        else:
            sys.stdout.write(".")
            time_started += 1
            #sys.stdout.write(network.state_str)
            #sys.stdout.write("(")
            #sys.stdout.write(str(network.nodes_count))
            #sys.stdout.write(")")
            #sys.stdout.write(".")
            sys.stdout.flush()
            time.sleep(1.0)
    
    
    #print("Memory use : {} Mo".format( (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0)))
    if not network.is_ready:
        print(".")
        print("Network is not ready but continue anyway")
    
    print("------------------------------------------------------------")
    print("Controller capabilities : {}".format(network.controller.capabilities))
    print("Controller node capabilities : {}".format(network.controller.node.capabilities))
    print("Nodes in network : {}".format(network.nodes_count))
    print("Driver statistics : {}".format(network.controller.stats))
    print("------------------------------------------------------------")
    
    print("------------------------------------------------------------")
    print("Driver statistics : {}".format(network.controller.stats))
    print("------------------------------------------------------------")
    
    print("------------------------------------------------------------")
    print("Try to autodetect nodes on the network")
    print("------------------------------------------------------------")
    print("Nodes in network : {}".format(network.nodes_count))
    print("------------------------------------------------------------")
    print("Retrieve switches on the network")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_switches() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  state: {}".format(network.nodes[node].get_switch_state(val)))
    print("------------------------------------------------------------")
    print("Retrieve dimmers on the network")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_dimmers() :
            print("node/name/index/instance : {}/{}/{}/{}".format (node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format (network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format (network.nodes[node].values[val].id_on_network))
            print("  level: {}".format (network.nodes[node].get_dimmer_level(val)))
            global Lamp_node
            Lamp_node = node
            
    print("------------------------------------------------------------")
    print("Retrieve RGB Bulbs on the network")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_rgbbulbs() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  level: {}".format(network.nodes[node].get_dimmer_level(val)))
    print("------------------------------------------------------------")
    print("Retrieve sensors on the network")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_sensors() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  value: {} {}".format(network.nodes[node].get_sensor_value(val), network.nodes[node].values[val].units))
            global Multisensor_node
            Multisensor_node = node
          
    print("------------------------------------------------------------")
    print("Retrieve thermostats on the network")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_thermostats() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  value: {} {}".format(network.nodes[node].get_thermostat_value(val), network.nodes[node].values[val].units))
    print("------------------------------------------------------------")
    print("Retrieve switches all compatibles devices on the network    ")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_switches_all() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  value / items:  / {}".format(network.nodes[node].get_switch_all_item(val), network.nodes[node].get_switch_all_items(val)))
            print("  state: {}".format(network.nodes[node].get_switch_all_state(val)))
    print("------------------------------------------------------------")
    print("------------------------------------------------------------")
    print("Retrieve protection compatibles devices on the network    ")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_protections() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : ".format(network.nodes[node].values[val].id_on_network))
            print("  value / items: {} / {}".format(network.nodes[node].get_protection_item(val), network.nodes[node].get_protection_items(val)))
    print("------------------------------------------------------------")
    
    print("------------------------------------------------------------")
    print("Retrieve battery compatibles devices on the network         ")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_battery_levels() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  value : {}".format(network.nodes[node].get_battery_level(val)))
    print("------------------------------------------------------------")
    
    print("------------------------------------------------------------")
    print("Retrieve power level compatibles devices on the network         ")
    print("------------------------------------------------------------")
    values = {}
    for node in network.nodes:
        for val in network.nodes[node].get_power_levels() :
            print("node/name/index/instance : {}/{}/{}/{}".format(node,network.nodes[node].name,network.nodes[node].values[val].index,network.nodes[node].values[val].instance))
            print("  label/help : {}/{}".format(network.nodes[node].values[val].label,network.nodes[node].values[val].help))
            print("  id on the network : {}".format(network.nodes[node].values[val].id_on_network))
            print("  value : {}".format(network.nodes[node].get_power_level(val)))
    print("------------------------------------------------------------")
    #print
    #print("------------------------------------------------------------")
    #print "Activate the switches on the network"
    #print "Nodes in network : {}".format network.nodes_count
    #print("------------------------------------------------------------")
    #for node in network.nodes:
    #    for val in network.nodes[node].get_switches() :
    #        print("Activate switch {} on node {}".format \
    #                (network.nodes[node].values[val].label,node))
    #        network.nodes[node].set_switch(val,True)
    #        print("Sleep 10 seconds")
    #        time.sleep(10.0)
    #        print("Dectivate switch {} on node {}".format \
    #                (network.nodes[node].values[val].label,node))
    #        network.nodes[node].set_switch(val,False)
    #print("Done"))
    #print("------------------------------------------------------------")
        
    
    

def config_sensors():
 
    network.nodes[Multisensor_node].set_config_param(100,0)
    
    #network.nodes[Multisensor_node].set_config_param(111, 5)
    #network.nodes[Multisensor_node].set_config_param(112, 5)
    #network.nodes[Multisensor_node].set_config_param(113, 5)
    network.nodes[Multisensor_node].set_config_param(3, 10)


######################################################################
## FUNCTIONS FOR MQTT ################################################
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


class Device(object):
    """Represents the state of a single device."""

    def __init__(self):
        self.temperature = 0
        self.humidity = 0
        self.luminance = 0
        self.sensor = -1
        self.connected = False
        self.lamp01_state = 0
        self.lamp01_set = 0
      
    def get_devices_data(self):
        
       
        for val in network.nodes[Multisensor_node].get_sensors() :
            print("  {}: {} {}".format(network.nodes[Multisensor_node].values[val].label, round(network.nodes[Multisensor_node].get_sensor_value(val),1), network.nodes[Multisensor_node].values[val].units))
            if network.nodes[Multisensor_node].values[val].label =="Temperature":
              self.temperature = round(network.nodes[Multisensor_node].get_sensor_value(val),1)
            elif network.nodes[Multisensor_node].values[val].label =="Relative Humidity":
              self.humidity = network.nodes[Multisensor_node].get_sensor_value(val)
            elif network.nodes[Multisensor_node].values[val].label =="Luminance":
              self.luminance = network.nodes[Multisensor_node].get_sensor_value(val)
            elif network.nodes[Multisensor_node].values[val].label =="Sensor":
              self.sensor = network.nodes[Multisensor_node].get_sensor_value(val)
        
        
        for val in network.nodes[Lamp_node].get_dimmers() :
            print("  {}: {} {}".format(network.nodes[Lamp_node].values[val].label, round(network.nodes[Lamp_node].get_dimmer_level(val),1), network.nodes[Lamp_node].values[val].units))
            #if network.nodes[Lamp_node].values[val].label =="":
            self.lamp01_state = round(network.nodes[Lamp_node].get_dimmer_level(val),1)
           
      
    def read_message(self, payload):
        
        if payload['type'] == 'config':
            device = payload['device']
            value = payload['value']

            if device == 'lamp01':
              self.lamp01_set = value
              
              for node in network.nodes:
                  for val in network.nodes[node].get_dimmers() :
                      print("Activate dimmer : {} {}".format(network.nodes[node], val))
                      network.nodes[node].set_dimmer(val,value)
                            
            
            print()
            print("*****Configuring Lamp {} with value {}.*****"
                  .format(device, self.lamp01_set))   
        
        

    def wait_for_connection(self, timeout):
        """Wait for the device to become connected."""
        total_time = 0
        while not self.connected and total_time < timeout:
            time.sleep(1)
            total_time += 1

        if not self.connected:
            raise RuntimeError('Could not connect to MQTT bridge.')

    def on_connect(self, unused_client, unused_userdata, unused_flags, rc):
        """Callback for when a device connects."""
        print('Connection Result:', error_str(rc))
        self.connected = True

    def on_disconnect(self, unused_client, unused_userdata, rc):
        """Callback for when a device disconnects."""
        print('Disconnected:', error_str(rc))
        self.connected = False

    def on_publish(self, unused_client, unused_userdata, unused_mid):
        """Callback when the device receives a PUBACK from the MQTT bridge."""
        print('Published message acked.')

    def on_subscribe(self, unused_client, unused_userdata, unused_mid,
                     granted_qos):
        """Callback when the device receives a SUBACK from the MQTT bridge."""
        print('Subscribed: ', granted_qos)
        if granted_qos[0] == 128:
            print('Subscription failed.')

    def on_message(self, unused_client, unused_userdata, message):
        """Callback when the device receives a message on a subscription."""
        payload = message.payload.decode('utf-8')
        print('Received message \'{}\' on topic \'{}\' with Qos {}'.format(
            payload, message.topic, str(message.qos)))

        # The device will receive its latest config when it subscribes to the
        # config topic. If there is no configuration for the device, the device
        # will receive a config with an empty payload.
        if not payload:
            return

        # The config is passed in the payload of the message. In this example,
        # the server sends a serialized JSON string.
        data = json.loads(payload)
        
        
        
        self.read_message(data)
        
        

def parse_command_line_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Example Google Cloud IoT MQTT device connection code.')
    parser.add_argument(
        '--project_id',
        default=project_id,#os.environ.get("GOOGLE_CLOUD_PROJECT"),
        required=False,
        help='GCP cloud project name.')
    parser.add_argument(
        '--registry_id',default=registry_id, required=False, help='Cloud IoT registry id')
    parser.add_argument(
        '--device_id',default=device_id,
        required=False,
        help='Cloud IoT device id')
    parser.add_argument(
        '--topic',default=topic,
        required=False,
        help='Pub/Sub topic')
    parser.add_argument(
        '--private_key_file',default=private_key_file, required=False, help='Path to private key file.')
    parser.add_argument(
        '--algorithm', default=algorithm,
        choices=('RS256', 'ES256'),
        required=False,
        help='Which encryption algorithm to use to generate the JWT.')
    parser.add_argument(
        '--cloud_region', default=cloud_region, help='GCP cloud region')
    parser.add_argument(
        '--ca_certs',
        default='roots.pem',
        help='CA root certificate. Get from https://pki.google.com/roots.pem')
    parser.add_argument(
        '--num_messages',
        type=int,
        default=100,
        help='Number of messages to publish.')
    parser.add_argument(
        '--mqtt_bridge_hostname',
        default='mqtt.googleapis.com',
        help='MQTT bridge hostname.')
    parser.add_argument(
        '--mqtt_bridge_port', type=int, default=8883, help='MQTT bridge port.')
    parser.add_argument(
        '--message_type', choices=('event', 'state'),
        default='state',
        help=('Indicates whether the message to be published is a '
              'telemetry event or a device state message.'))

    return parser.parse_args()


def main():
    args = parse_command_line_args()

    # Create the MQTT client and connect to Cloud IoT.
    client = mqtt.Client(
        client_id='projects/{}/locations/{}/registries/{}/devices/{}'.format(
            args.project_id,
            args.cloud_region,
            args.registry_id,
            args.device_id))
    client.username_pw_set(
        username='unused',
        password=create_jwt(
            args.project_id,
            args.private_key_file,
            args.algorithm))
    client.tls_set(ca_certs=args.ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)

    print("Reaching telemetry : ", end = '')
    mqtt_telemetry_topic = '/devices/{}/events/{}'.format(args.device_id, args.topic)
    print(mqtt_telemetry_topic)
    print("Reaching config : ", end = '')
    mqtt_config_topic = '/devices/{}/config'.format(args.device_id)
    print(mqtt_config_topic)
    
    
    start_network()
    
    if ((Multisensor_node ==-1) or (Lamp_node ==-1)):
      print("The multisensor or the lamp are not connected!")
      print("Existing, restart again")
      exit()
      
    config_sensors()
    
    device = Device()


    client.on_connect = device.on_connect
    client.on_publish = device.on_publish
    client.on_disconnect = device.on_disconnect
    client.on_subscribe = device.on_subscribe
    client.on_message = device.on_message
    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)
    
    client.loop_start()

  
    
    
    # Wait up to 5 seconds for the device to connect.
    device.wait_for_connection(5)

    # Subscribe to the config topic.
    client.subscribe(mqtt_config_topic, qos=0)

    try:
      # Update and publish sensors readings at a rate of one per 5 second.
      while(1):
        
        network.nodes[Multisensor_node].request_state()
        network.nodes[Lamp_node].request_state()
          
        time.sleep(5)
        device.get_devices_data()
    
        # Report the device's temperature to the server by serializing it
        # as a JSON string.
        
        payload = json.dumps({"SENSOR01" : {"Presence" : device.sensor, 
                                             "Temperature" : device.temperature, 
                                             "Humidity" : device.humidity, 
                                             "Luminosity" : device.luminance},
                                             "LAMP01" : {"real_val" : device.lamp01_state,
                                             "set_val" : device.lamp01_set} 
                                             })
        print('Publishing payload', payload)
        client.publish(mqtt_telemetry_topic, payload, qos=1)
      
    except KeyboardInterrupt:
        print('\nRe-initialising device configuration')
        payload = json.dumps({'zErrorCode' : 'INTERRUPT REINIT'})
        client.publish(mqtt_telemetry_topic, payload, qos = 1)
        print('Re-initialisation done. Exiting.')
        client.disconnect()
        client.loop_stop()
         


if __name__ == '__main__':
    main()
