import logging
logging.basicConfig(level=logging.INFO)
import azure.functions as func
import requests
import os
import datetime
import pytz

#TODO: add schedule to run this every hour between 6 and 20 between may and august

#TODO: map the blinds to the direction of the sun according to the current month
device_id = 'fcb467a615c0'

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

    if sunrise_time.hour <= current_hour <= sunset_time.hour:
        logging.info(f'The sun will shine at {current_hour}:00.')

        #TODO: Check if the blinds are already closed

        # close the blinds
        shelly_auth = os.getenv('SHELLY_AUTH_TOKEN')

        payload = {
            'channel': '1',
            'turn': 'on',
            'id': device_id,
            'auth_key': shelly_auth
        }
        response = requests.post(f'https://shelly-27-eu.shelly.cloud/device/relay/control', data=payload)
        if response.status_code == 200:
            logging.info(f'Closing {device_id}.')
        else:
            logging.error(f'Failed to close blind {device_id} switch. Error: {response.text}')

    else:
        logging.info(f'The sun will not shine at {current_hour}:00.')
        #TODO: open blinds if closed and shouldn't be
    
#TODO: send a mail or telegram on error