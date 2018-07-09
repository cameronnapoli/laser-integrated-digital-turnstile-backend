# Senior Design Backend - Laser Integrated Digital Turnstile system (LIDT)
REST API for senior design project. Written using the Python Flask framework.

## Dependencies

* python 2.7.14
* Flask 0.12.2
* Flask-cors 3.0.6
* MySQL-python 1.2.5

## Usage

Run on localhost:5000 with:
```
python application.py
```

## API Endpoints

### Generate Auth Token
```
/gen_auth_token
```
#### Description
Generate an authentication token to be passed into subsequent API calls.


### Register Event
```
/register_event
```
#### Description
Register an event to the MySQL DB from a sending device.


### Debug Preview
```
/debug_preview
```
#### Description
Print formatted HTML debug info for a specific device.


### Get All Client Devices
```
/GetAllClientDevices
```
#### Description
Get all device ID's associated with a certain client.


### Get Device Count
```
/GetDeviceCount
```
#### Description
Get number of entry events and exit events for a certain device.


### Get All Device Count History
```
/GetAllDeviceCountHistory
```
#### Description
Group device entries and exits over a certain interval at the specified subinterval.


### Add Device
```
/AddDevice
```
#### Description
Add a device to the MySQL DB.


### Add User
```
/AddUser
```
#### Description
Add a user to the MySQL DB.
