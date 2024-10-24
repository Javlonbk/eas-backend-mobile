import requests

BASE_URL = "http://192.168.21.75:5000/api/v4.2/defend/"

def start_def(token, duration, sensor):
    url = BASE_URL + sensor
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Authorization": token,
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "http://192.168.21.75",
        "Referer": "http://192.168.21.75/",
        "User-Agent": "USER AGENT"
    }
    payload = {
        "auto": False,
        "frequencies": ["2.4GHz", "5.2GHz", "5.8GHz", "433MHz", "915MHz", "1.2GHz", "1.5GHz"],
        "duration": duration,
        "gnss_jamming": True,
        "delay": duration/10,
        "azimuth": 0
    }

    response = requests.post(url, json=payload, headers=headers)
    
    print("STATUS CODE .....:", response.status_code)
    print(token)
    return response

def stop_def(token, sensor):
    url = BASE_URL + sensor
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Authorization": token,
        "Connection": "keep-alive",
        "Origin": "http://192.168.21.75",
        "Referer": "http://192.168.21.75/",
        "User-Agent": "USER AGENT"
    }

    response = requests.delete(url, headers=headers)
    
    print("STATUS CODE", response.status_code)
    return response