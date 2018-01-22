# senior-design-backend
REST API for senior design project. Written with Flask framework.

## Dependencies

* python 2.7.14
* Flask 0.12.2
* MySQL-python 1.2.5

## Usage

Run on localhost:5000 with:
```
python app.py
```

## API

### Register Event
```
/register_event
```
POST request
#### Headers
```
auth-token : for now leave as empty string
```
#### Body
JSON object with keys eventType and deviceID. For example:
```
{
  "eventType" : "exit",
  "deviceID" : 1234
}
```
