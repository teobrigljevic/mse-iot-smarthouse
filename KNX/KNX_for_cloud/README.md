*********************************************************************
INSTALL KNXNET:
*************************************************
***On first use:

sudo apt-get update

sudo apt-get install python3-setuptools

cd knxnet_iot

sudo python3 setup.py install
*************************************************
***Next uses:

cd knxnet_iot

sudo python3 setup.py install
*********************************************************************
*********************************************************************
INSTALL REQUIREMENTS IN VIRTUAL ENV:
*************************************************
***In root folder (KNX_for_cloud)

virtualenv env

source env/bin/activate

pip3 install -r requirements.txt
*********************************************************************
*********************************************************************
RUNNING THE KNX-CLIENT.PY SCRIPT:
*************************************************
python3 knx-client-cloud.py PROJECT_ID REGISTRY_ID DEVICE_ID TOPIC KEY_PATH ALGORITHM

python3 knx-client-cloud.py smarthouseiot-261017 smarthouse serverKNX room01k rsa_private.pem RS256
