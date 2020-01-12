import base64
import json
import datetime

from google.cloud import iot_v1
from google.cloud import firestore

project_id = 'smarthouseiot-261017'
cloud_region = 'europe-west1'
registry_id = 'smarthouse'
device_id = 'serverKNX'
collection_name = 'ROOM02'
history_name = collection_name + '_HISTORY'
devices_names = {'Blind10' : 'kBLIND01', 'Blind11' : 'kBLIND02', 'Valve10' : 'kVALVE01', 'Valve11' : 'kVALVE02'}
initialisation_name = '0kINIT'
parameters_name = '0kSETPARAM'
sensor_name = 'zSENSOR01'
version = 0
retention_days = 5

def check_db(collection):
    checks = [False]*len(devices_names)
    devices = sorted(list(devices_names))
    
    for device in devices:
        device_ref = collection.document(devices_names[device])
        try:
            device_snap = device_ref.get()
            checks[devices.index(device)] = True
        except google.cloud.exceptions.NotFound:
            print('LOG: Error reading {} !'.format(device))

    return checks

def command(collection, h_m):
    command_result = {'Update' : False, 'Blinds' : [], 'Valves' : []}
    
    devices = sorted(list(devices_names))
    for device in devices:
        if(device.find('Blind') > -1):
            command_result['Blinds'].append(-1)
        if(device.find('Valve') > -1):
            command_result['Valves'].append(-1)    
    
    db_kinit_ref = collection.document(initialisation_name)
    try:
        db_kinit_snap = db_kinit_ref.get()
    except google.cloud.exceptions.NotFound:
        print('LOG: No initilisation parameters found ! Exiting...')
        return command_result
    db_kinit = db_kinit_snap.to_dict()
    
    db_kparam_ref = collection.document(parameters_name)
    try:
        db_kparam_snap = db_kparam_ref.get()
    except google.cloud.exceptions.NotFound:
        print('LOG: No room parameters found ! Exiting...')
        return command_result
    db_kparam = db_kparam_snap.to_dict()
    
    db_zmeas_ref = collection.document(sensor_name)
    try:
        db_zmeas_snap = db_zmeas_ref.get()
    except google.cloud.expcetions.NotFound:
        print('LOG: No sensor file found ! Exiting...')
        return command_result
    db_zmeas = db_zmeas_snap.to_dict()
    
    user_override = db_kparam['UserOverride']
    user_pres = db_zmeas['Presence']
    
    set_values = []
    real_values = []
    
    checks = check_db(collection)
    
    for check, device in zip(checks, devices):
        if check:
            device_meas = collection.document(devices_names[device]).get().to_dict()
            if(device.find('Blind') > -1):
                real_value = device_meas['RealVal']
                set_value = device_meas['SetVal']
                command_result['Blinds'][int(devices_names[device][-1])-1] = real_value
                real_values.append(real_value)
                set_values.append(set_value)
            if(device.find('Valve') > -1):
                real_value = device_meas['RealVal']
                set_value = device_meas['SetVal']
                command_result['Valves'][int(devices_names[device][-1])-1] = real_value
                real_values.append(real_value)
                set_values.append(set_value)

    if user_pres:
        print('LOG: The room is currently occupied !')
    
    if user_override:
        print('LOG: The room is available for manual commands !')
        
        for device, set_value in zip(devices, set_values):
            if(device.find('Blind') > -1):
                if(db_kinit['Blinds']['InitVal'][device] != set_value):
                    command_result['Blinds'][int(devices_names[device][-1])-1] = set_value
            if(device.find('Valve') > -1):
                if(db_kinit['Valves']['InitVal'][device] != set_value):
                    command_result['Valves'][int(devices_names[device][-1])-1] = set_value
            
        if not user_pres:
            db_kparam_ref.update({u'UserOverride' : False})
            print('LOG: The room is currently empty !')
        
    else:
        print('LOG: Commands are set following the automatic logic !')
        
        temp_high = db_kparam['TemperatureHigh']
        temp_low = db_kparam['TemperatureLow']
        lum_low = db_kparam['LuminosityLow']
        hum_high = db_kparam['HumidityHigh']
        hum_low = db_kparam['HumidityLow']
        
        temp_meas = db_zmeas['Temperature']
        lum_meas = db_zmeas['Luminosity']
        hum_meas = db_zmeas['Humidity']
        
        if user_pres:
            if temp_meas < temp_low:
                command_result['Valves'] = [255 for valve in command_result['Valves']]
            if temp_meas > temp_high:
                command_result['Valves'] = [100 for valve in command_result['Valves']]
            hour = h_m // 100
            if((lum_meas < lum_low) and
               ((hour > 7) and (hour < 18))):
                command_result['Blinds'] = [255 for valve in command_result['Blinds']]
        else:
            if temp_meas > temp_high:
                command_result['Valves'] = [60 for valve in command_result['Valves']]
            if temp_meas < temp_low:
                command_result['Valves'] = [120 for valve in command_result['Valves']]
            if hum_meas > hum_high:
                command_result['Blinds'] = [0 for valve in command_result['Blinds']]
            if hum_meas < hum_low:
                command_result['Blinds'] = [110 for valve in command_result['Blinds']]

    if(real_values != (command_result['Blinds'] + command_result['Valves'])):
        command_result['Update'] = True
                
    return command_result    

def knx_func(event, context):
    
    time = context.timestamp
    y_m_d = time.split('T')[0].split('-')
    h_m = time.split('T')[1].split(':')
    
    clt = iot_v1.DeviceManagerClient()
    device_path = clt.device_path(project_id, cloud_region, registry_id, device_id)
    
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    message = json.loads(pubsub_message)
    
    db = firestore.Client()
    collection_ref = db.collection(collection_name)
    try:
        collection = collection_ref.get()
    except google.cloud.exceptions.NotFound:
        print('LOG: No collection ROOM01 found ! Exiting...')
        return 0
    history_ref = db.collection(history_name)
    try:
        history = history_ref.get()
    except google.cloud.exceptions.NotFound:
        print('LOG: No collection ROOM02_HISTORY found ! Exiting...')
        return 0

    y_m_d = int(y_m_d[0] + y_m_d[1] + y_m_d[2])
    h_m = int(h_m[0] + h_m[1])
    if ((h_m > 2300) and (h_m < 2302)):
        docs = history_ref.where(u'kDATE', u'<', (today-retention_days)).stream()
        for doc in docs:
            doc.reference.delete()
            
    if message['kErrorCode'] == 'NO CONFIGURATION':
        
        print('LOG: Setting device configuration !')  
        
        init_ref = collection_ref.document(initialisation_name)
        try:
            init_data_snap = init_ref.get()
        except google.cloud.exceptions.NotFound:
            print('LOG: Error reading initialisation document ! Exiting...')
            return 0
        
        init_dict = init_data_snap.to_dict()
        gateway = init_dict['Gateway']
        endpoint = init_dict['Endpoint']
        
        blinds_id_dict = init_dict['Blinds']['Id']
        blinds_id_sort = sorted(blinds_id_dict.keys())
        blinds_id = [blinds_id_dict[key] for key in blinds_id_sort]
        blinds_val_dict = init_dict['Blinds']['InitVal']
        blinds_val_sort = sorted(blinds_val_dict.keys())
        blinds_val = [blinds_val_dict[key] for key in blinds_val_sort]
        
        valves_id_dict = init_dict['Valves']['Id']
        valves_id_sort = sorted(valves_id_dict.keys())
        valves_id = [valves_id_dict[key] for key in valves_id_sort]
        valves_val_dict = init_dict['Valves']['InitVal']
        valves_val_sort = sorted(valves_val_dict.keys())
        valves_val = [valves_val_dict[key] for key in valves_val_sort]
        
        devices = sorted(list(devices_names))
        checks = check_db(collection_ref)
        for check, device in zip(checks, devices):
            if check:
                device_ref = collection_ref.document(devices_names[device])
                if(device.find('Blind') > -1):
                    device_ref.update({u'SetVal' : blinds_val[int(devices_names[device][-1])-1]})
                    device_ref.update({u'RealVal' : blinds_val[int(devices_names[device][-1])-1]})
                if(device.find('Valve') > -1):
                    device_ref.update({u'SetVal' : valves_val[int(devices_names[device][-1])-1]})
                    device_ref.update({u'RealVal' : valves_val[int(devices_names[device][-1])-1]})

        config = {}
        config["type"] = "config"
        config["room"] = int(collection_name[-1])
        config["gateway"] = gateway
        config["endpoint"] = endpoint
        config["targets"] = {}
        config["targets"]["blinds"] = {}
        config["targets"]["blinds"]["id"] = blinds_id
        config["targets"]["blinds"]["val"] = blinds_val
        config["targets"]["valves"] = {}
        config["targets"]["valves"]["id"] = valves_id
        config["targets"]["valves"]["val"] = valves_val
        
        config = str(config)
        config = config.replace('\'', '"')        
        data = str(config).encode('utf-8')
        
        return clt.modify_cloud_to_device_config(device_path, data, version)
    
    if message['kErrorCode'] == 'CONFIGURATION UPDATED':
        print('LOG: Acknowledging device configuration updated !')
    
    if message['kErrorCode'] == 'CURRENT STATUS':
        
        status = {}
        status['BLIND01'] = message['blind10']
        status['BLIND02'] = message['blind11']
        status['VALVE01'] = message['valve10']
        status['VALVE02'] = message['valve11']
        status['kDATE'] = y_m_d
        
        document_name = time + '_k'
        history_ref.document(document_name).set(status)

        devices = sorted(list(devices_names))
        checks = check_db(collection_ref)
        for check, device in zip(checks, devices):
            if check:
                device_ref = collection_ref.document(devices_names[device])
                if(device.find('Blind') > -1):
                    device_ref.update({u'RealVal' : message[device.lower()]['real_val']})
                if(device.find('Valve') > -1):
                    device_ref.update({u'RealVal' : message[device.lower()]['real_val']})
        
        print('LOG: Saving current KNX status !')
        
    if message['kErrorCode'] == 'WAITING ON COMMAND':
        command_res = command(collection_ref, h_m)
        
        if command_res['Update']:
            print('LOG: Sending updated configuration !')
            
            config = {}
            config["type"] = "update"
            config["room"] = int(collection_name[-1])
            config["data"] = {}
            config["data"]["blinds"] = command_res['Blinds']
            config["data"]["valves"] = command_res['Valves']
            
            config = str(config)
            config = config.replace('\'', '"')
            data = str(config).encode('utf-8')
            
            return clt.modify_cloud_to_device_config(device_path, data, version)
        
        else:
            print('LOG: No updated configuration to send !')
            
    if message['kErrorCode'] == 'INTERRUPT REINIT':
        
        today = y_m_d
        
        docs = history_ref.where(u'kDATE', u'<', (today-retention_days)).stream()
        for doc in docs:
            doc.reference.delete()
            
        docs = history_ref.where(u'zDATE', u'<', (today-retention_days)).stream()
        for doc in docs:
            doc.reference.delete()
            
        print('LOG: Re-initialising device configuration on KNX interrupt !')
        
        document_name = time + '_k'
        history_ref.document(document_name).set(message)
        
        config = ''
        config = str(config)
        data = str(config).encode('utf-8')
        return clt.modify_cloud_to_device_config(device_path, data, version)
