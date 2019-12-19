*********************************************************************
INSTALL KNXNET:
*************************************************
On first use:

sudo apt-get update

sudo apt-get install python3-setuptools

cd knxnet_iot

sudo python3 setup.py install
*************************************************
Next uses:

cd knxnet_iot

sudo python3 setup.py install
*********************************************************************
*********************************************************************
RUNNING THE KNX-CLIENT.PY SCRIPT:
*************************************************
python3 knx-client.py PROJECT_ID REGISTRY_ID DEVICE_ID KEY_PATH ALGORITHM

python3 knx-client.py PROJECT_ID REGISTRY_ID DEVICE_ID KEY_PATH ALGORITHM
