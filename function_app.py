import logging
logging.basicConfig(level=logging.INFO)
import azure.functions as func
import requests
import os
import datetime
import pytz
import time

#TODO: add schedule to run this every hour between 6 and 20 between may and august

#list of all devices/blinds/switches and there orientation regarding the sun relative to the house
all_device_ids = [
    ['fcb467a615c0', 'East', 'Küche'],
    ['fcb467a5c794', 'East', 'Klavier'],
    ['fcb467a59c88', 'South', 'Essen'],
    ['fcb467a5d358', 'South', 'Wohnen'],
    ['fcb467a5b4f0', 'West', 'Terrasse'],
    ['fcb467a683c8', 'West', 'Gästebad']
]

#list of all hours of the day when the sun shines mapped to the direction from where it shines
sun_direction = {
    6: 'East',
    7: 'East',
    8: 'East',
    9: 'East',
    10: 'South',
    11: 'South',
    12: 'South',
    13: 'South',
    14: 'South',
    15: 'West',
    16: 'West',
    17: 'West',
    18: 'West',
    19: 'West',
    20: 'West'
}

# prepare weather forecast request
berlin_tz = pytz.timezone('Europe/Berlin')
current_time = datetime.datetime.now(tz=berlin_tz)
current_hour = current_time.hour
city = 'Schmölln-Putzkau, DE'
logging.info(f'Checking sunshine forecast for {city} at {current_hour}.')

# get the weather forecast for the current hour, to see whether the sun will shine
api_key = os.getenv('OPENWEATHERMAP_API_KEY')
response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}')
weather_data = response.json()

if 'weather' in weather_data:
    sunrise_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunrise'], tz=berlin_tz)
    sunset_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunset'], tz=berlin_tz)
    shelly_auth = os.getenv('SHELLY_AUTH_TOKEN')
    #iterate over the devices and check whether the sun will shine at the current hour and the window is impacted
    #if so, tell it to close, if not, tell it to open
    for device_id, device_direction, device_name in all_device_ids:
        if device_direction == sun_direction[current_hour] and sunrise_time.hour <= current_hour <= sunset_time.hour:
            logging.info(f'The sun will shine at {current_hour}:00 for {device_name}, closing the blind.')
            channel = "1"
        else:
            logging.info(f'The sun will not shine at {current_hour}:00 for {device_name}, opening the blind.')
            channel = "0"

        # prepare device payload
        payload_str = f"channel={channel}&turn=on&id={device_id}&auth_key={shelly_auth}"
        logging.info(f'Payload: {payload_str}')

        headers = {'content-type': 'application/x-www-form-urlencoded'}
        response = requests.post(f'https://shelly-27-eu.shelly.cloud/device/relay/control', data=payload_str, headers=headers)

        if response.status_code == 200:
            logging.info(f'Request sent successfully for {device_name}.')
        else:
            logging.error(f'Failed to control {device_name}. Error: {response.text}')
        
        time.sleep(10) #wait for 10 second before sending the next request to avoid rate limit
    
    logging.info('All blinds set according to forecast, see you next hour.')

else:
    logging.error('Failed to fetch or read weather data - mission abort.')    

#TODO: send a mail or telegram on error