import requests
import csv
from datetime import datetime, timedelta
from scipy.interpolate import interp1d

def download_weather_data(api_key, location, geolocation, start_date, end_date, output_file):
    url = f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={geolocation[0]}&lon={geolocation[1]}&appid={api_key}&start={start_date}&end={end_date}"
    response = requests.get(url)
    data = response.json()

    # Create a dictionary to store the hourly data
    hourly_data = {}
    for entry in data['hourly']:
        dt = datetime.fromtimestamp(entry['dt'])
        hourly_data[dt] = {
            'temp': entry['temp'],
            'pressure': entry['pressure'],
            'humidity': entry['humidity'],
            'wind_speed': entry['wind_speed'],
            'wind_deg': entry['wind_deg']
        }

    # Fill in missing data
    for dt in hourly_data.keys():
        for key in hourly_data[dt].keys():
            if hourly_data[dt][key] is None:
                # Find the nearest non-null value
                prev_dt = dt - timedelta(hours=1)
                next_dt = dt + timedelta(hours=1)
                while prev_dt not in hourly_data or hourly_data[prev_dt][key] is None:
                    prev_dt -= timedelta(hours=1)
                while next_dt not in hourly_data or hourly_data[next_dt][key] is None:
                    next_dt += timedelta(hours=1)
                # Interpolate the missing value
                prev_val = hourly_data[prev_dt][key]
                next_val = hourly_data[next_dt][key]
                interp_func = interp1d([prev_dt.timestamp(), next_dt.timestamp()], [prev_val, next_val], fill_value='extrapolate')
                hourly_data[dt][key] = interp_func(dt.timestamp())

    # Interpolate to 15 minute intervals
    start_dt = datetime.fromtimestamp(data['hourly'][0]['dt'])
    end_dt = datetime.fromtimestamp(data['hourly'][-1]['dt'])
    new_data = []
    for dt in hourly_data.keys():
        if dt < start_dt or dt > end_dt:
            continue
        new_data.append([
            dt.strftime('%Y-%m-%d %H:%M:%S'),
            hourly_data[dt]['temp'],
            hourly_data[dt]['pressure'],
            hourly_data[dt]['humidity'],
            hourly_data[dt]['wind_speed'],
            hourly_data[dt]['wind_deg']
        ])
    interp_func = interp1d([datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S').timestamp() for row in new_data], [row[1:] for row in new_data], axis=0, fill_value='extrapolate')
    new_dt = start_dt
    while new_dt <= end_dt:
        new_row = [new_dt.strftime('%Y-%m-%d %H:%M:%S')] + interp_func(new_dt.timestamp()).tolist()
        new_data.append(new_row)
        new_dt += timedelta(minutes=15)

    # Write the data to a CSV file
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Date', 'Temperature', 'Pressure', 'Humidity', 'Wind Speed', 'Wind Direction'])
        for row in new_data:
            writer.writerow(row)

