import base64
import datetime
import json
from google.cloud import iot_v1
from google.cloud import firestore

project_id = 'smarthouseiot-261017'
cloud_region = 'europe-west1'
registry_id = 'smarthouse'
device_id = 'serverZWAVE'
collection_name = 'ROOM01'
history_name = collection_name + '_HISTORY'
version = 0
retention_days = 5

def zwave_func(event, context):
    
    time = context.timestamp
    y_m_d = time.split('T')[0].split('-')
    h_m = time.split('T')[1].split(':')
    
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
        print('LOG: No collection ROOM01_HISTORY found ! Exiting...')
        return 0
    
    y_m_d = int(y_m_d[0] + y_m_d[1] + y_m_d[2])
    h_m = int(h_m[0] + h_m[1])
    if ((h_m > 2300) and (h_m < 2302)):
        docs = history_ref.where(u'zDATE', u'<', (today-retention_days)).stream()
        for doc in docs:
            doc.reference.delete()
            
    status = {}
    status['SENSOR01'] = message['SENSOR01']
    status['LAMP01'] = message['LAMP01']
    status['zDATE'] = y_m_d
    
    document =  time + '_z'
    db.collection(history_name).document(document).set(status)
    
    temp = message["LAMP01"]
    del message["LAMP01"]
    db.collection(collection_name).document(u'zLAMP01').update({u'RealVal' : temp["real_val"]})
    for sensors in message:
        print("Sensor found:" + sensors)
        db.collection(collection_name).document('z'+sensors).set(message[sensors])
        
    db_zparam = db.collection(collection_name).document(u'zLAMP01').get().to_dict()
    realValue = db_zparam['RealVal']
    setValue = db_zparam['SetVal']
    
    if realValue != setValue:
    	clt = iot_v1.DeviceManagerClient()
    	device_path = clt.device_path(project_id, cloud_region, registry_id, device_id)
    
    	config = {}
    	config["type"] = "config"
    	config["device"] = "lamp01"
    	config["value"] = setValue

    	config = str(config)
    	config = config.replace('\'', '"')

    	data = str(config).encode('utf-8')

    	clt.modify_cloud_to_device_config(device_path, data, version)
