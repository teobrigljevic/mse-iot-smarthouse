# KNX resources

This directory contains the files relevant for the KNX part of our project.

They are sorted as follows:

- KNX_basics:
  
  Source code for local KNX operations, working with the Actuasim simulator or the remote gateway located at the HEPIA
  
- KNX_for_cloud:
  
  Source code for the KNX operations linked with the Google Cloud infrastructure, implementing MQTT communication and working with the Actuasim simulator
  
- actuasim_iot:

  The actuasim simulator, obtained from the original repo `https://githepia.hesge.ch/adrienma.lescourt/actuasim_iot`

# Requirements

All the operations done with the KNX resources are done on a Linux Ubuntu 18_04_3 virtual machine using Virtual Box.

## KNXnet

Both the KNX_basic and the KNX_for_cloud resources require the knxnet_iot python library, available at `https://githepia.hesge.ch/adrienma.lescourt/knxnet_iot`.

### Installing KNXnet

- On first use:

  `sudo apt-get update`

  `sudo apt-get install python3-setuptools`

  `cd knxnet_iot`

  `sudo python3 setup.py install`

- On following uses:

  `cd knxnet_iot`
  
  `sudo python3 setup.py install`
  
## Actuasim

Both the KNX_basic and the KNX_for_cloud resources require the Actuasim simulator.

### Installting the Actuasim simulator

- On first use:
  `sudo apt-get update`
  
  `sudo apt-get install python3-pyqt5`
  
  `cd actuasim_iot`
  
  `python3 actuasim.py`
  
- Next uses:
  
  `cd actuasim_iot`
  
  `python3 actuasim.py`
  
## Requirements for the Cloud infrastructure

The KNX_for_cloud resources require a certain amount of additional dependencies. The requirements are available in the `requirements.txt` file.

For an easy set up, using a virtual environement is recommended:

  `virtualenv env`
  
  `source env/bin/activate`
  
  `pip3 install -r requirements.txt`
