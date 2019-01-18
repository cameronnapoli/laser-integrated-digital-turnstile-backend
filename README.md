# Laser Integrated Digital Turnstile System (LIDT)

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

REST API for laser integrated digital turnstile system used to track pedestrian traffic. Written using the Python Flask framework.

## Dependencies

* python 2.7.14
* Flask 0.12.2
* Flask-cors 3.0.6
* MySQL-python 1.2.5

## Usage

Run on localhost:80 with:
```
python application.py
```

To run pointing to localhost db and on localhost:5000 use 
```
python application.py --debug
```

<br />

# API Endpoints

## Generate Auth Token
    /gen_auth_token
#### Description
Generate an authentication token to be passed into subsequent API calls.

<br />

## Register Event
    /register_event
#### Description
Register an event to the MySQL DB from a sending device.

<br />

## Debug Preview
    /debug_preview
#### Description
Print formatted HTML debug info for a specific device.

<br />

## Get All Client Devices
    /GetAllClientDevices
#### Description
Get all device ID's associated with a certain client.

<br />

## Get Device Count
    /GetDeviceCount
#### Description
Get number of entry events and exit events for a certain device.

<br />

## Get All Device Count History
    /GetAllDeviceCountHistory
#### Description
Group device entries and exits over a certain interval at the specified subinterval.

<br />

## Add Device
    /AddDevice
#### Description
Add a device to the MySQL DB.

