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
    ['fcb467a5d358', 'West', 'Terrasse'],
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

shelly_auth = os.getenv('SHELLY_AUTH_TOKEN')

# Call the weather API
api_key = os.getenv('OPENWEATHERMAP_API_KEY')
city = 'Schmölln-Putzkau, DE'
response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}')
weather_data = response.json()

if 'weather' in weather_data:
    berlin_tz = pytz.timezone('Europe/Berlin')
    sunrise_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunrise'], tz=berlin_tz)
    sunset_time = datetime.datetime.fromtimestamp(weather_data['sys']['sunset'], tz=berlin_tz)
    current_time = datetime.datetime.now(tz=berlin_tz)
    current_hour = current_time.hour

    for device_id, device_direction, device_name in all_device_ids:
        if device_direction == sun_direction[current_hour] and sunrise_time.hour <= current_hour <= sunset_time.hour:
            logging.info(f'The sun will shine at {current_hour}:00.')
            channel = '2'
        else:
            logging.info(f'The sun will not shine at {current_hour}:00.')
            channel = '1'

        payload = {
            'channel': channel,
            'turn': 'on',
            'id': device_id,
            'auth_key': shelly_auth
        }
        response = requests.post(f'https://shelly-27-eu.shelly.cloud/device/relay/control', data=payload)
        if response.status_code == 200:
            if channel == '1':
                logging.info(f'Opening blinds for {device_name}.')
            else:
                logging.info(f'Closing blinds for {device_name}.')
        else:
            logging.error(f'Failed to open/close blind {device_name}. Error: {response.text}')
        
        time.sleep(60)  # Pause execution for 1 minute, to wait for blind to close or open
        # Disable switch again for next interaction
        payload = {
            'channel': channel,
            'turn': 'off',
            'id': device_id,
            'auth_key': shelly_auth
        }
        response = requests.post(f'https://shelly-27-eu.shelly.cloud/device/relay/control', data=payload)
        if response.status_code == 200:
            logging.info(f'Turning off {device_name} on channel {channel}.')
        else:
            logging.error(f'Failed to turn off {device_name} on channel {channel}. Error: {response.text}')
else:
    logging.error('Failed to fetch or read weather data.')    
    
#TODO: send a mail or telegram on error