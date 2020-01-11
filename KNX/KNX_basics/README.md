
INSTALLING KNXNET:
***************************************
On first use:
sudo apt-get update
sudo apt-get install python3-setuptools
cd knxnet_iot
sudo python3 setup.py install
***************************************
Next uses:
cd knxnet_iot
sudo python3 setup.py install
*********************************************************************
*********************************************************************
INSTALLING AND RUNNING THE SIMULATOR (ACTUASIM):
***************************************
On first use:
sudo apt-get update
sudo apt-get install python3-pyqt5
cd actuasim_iot
python3 actuasim.py
***************************************
Next uses:
cd actuasim_iot
python3 actuasim.py
*********************************************************************
*********************************************************************
INSTALLING REQUIREMENTS FOR MQTT:
***************************************
sudo pip install -r requirements.txt
