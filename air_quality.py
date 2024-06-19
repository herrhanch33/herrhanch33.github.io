import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

# Function to get yesterday's date in the required format (yyyy-mm-dd)
def get_yesterday_date():
    return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

# Function to get today's date in the required format (yyyy-mm-dd)
def get_today_date():
    return datetime.today().strftime('%Y-%m-%d')

# Function to parse float values with proper handling of None and "통신장애"
def parse_float(value):
    if value is None or value == '-' or value == '통신장애':
        return None
    return float(value)

# Function to fetch yesterday's air quality forecast
def get_yesterday_forecast():
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMinuDustFrcstDspth'
    params = {
        'searchDate': get_yesterday_date(),
        'returnType': 'xml',
        'serviceKey': '0VhV1TCbbcxMHlB6pjqzumOa+ijbCbzPHqzztrPb8suvYQVvyj6G6yjLc7bMyPvA3XxnaNv/2L5J8wOBn8P8ng==',
        'numOfRows': '100',
        'pageNo': '1'
    }
    response = requests.get(url, params=params)
    root = ET.fromstring(response.content)
    
    pm10_info = None
    o3_info = None
    latest_pm10_time = None
    latest_o3_time = None
    today_date = get_today_date()
    announcement_times = ["23시 발표", "17시 발표", "11시 발표", "05시 발표"]

    for item in root.iter('item'):
        inform_code = item.find('informCode').text
        inform_grade = item.find('informGrade').text
        inform_data = item.find('informData').text
        data_time = item.find('dataTime').text

        if inform_data == today_date:
            for announcement_time in announcement_times:
                if announcement_time in data_time:
                    if inform_code == 'PM10' and (latest_pm10_time is None or data_time > latest_pm10_time):
                        latest_pm10_time = data_time
                        grades = inform_grade.split(',')
                        for grade in grades:
                            region, level = grade.split(':')
                            if region.strip() == '경북':
                                pm10_info = level.strip()

                    if inform_code == 'O3' and (latest_o3_time is None or data_time > latest_o3_time):
                        latest_o3_time = data_time
                        grades = inform_grade.split(',')
                        for grade in grades:
                            region, level = grade.split(':')
                            if region.strip() == '경북':
                                o3_info = level.strip()

    return {
        'pm10_info': pm10_info,
        'o3_info': o3_info,
        'latest_pm10_time': latest_pm10_time,
        'latest_o3_time': latest_o3_time
    }

# Function to fetch real-time air quality data
def get_realtime_air_quality():
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty'
    params = {
        'stationName': '양덕동',
        'dataTerm': 'DAILY',
        'pageNo': '1',
        'numOfRows': '100',
        'returnType': 'xml',
        'serviceKey': '0VhV1TCbbcxMHlB6pjqzumOa+ijbCbzPHqzztrPb8suvYQVvyj6G6yjLc7bMyPvA3XxnaNv/2L5J8wOBn8P8ng==',
        'ver': '1.1'
    }
    response = requests.get(url, params=params)
    root = ET.fromstring(response.content)
    
    latest_pm10 = None
    latest_pm10_24hr = None
    latest_pm25 = None
    latest_pm25_24hr = None
    latest_o3 = None
    latest_time = None

    for item in root.iter('item'):
        data_time = item.find('dataTime').text

        pm10_value = parse_float(item.find('pm10Value').text)
        pm10_value_24hr = parse_float(item.find('pm10Value24').text)
        pm25_value = parse_float(item.find('pm25Value').text)
        pm25_value_24hr = parse_float(item.find('pm25Value24').text)
        o3_value = parse_float(item.find('o3Value').text)

        if any(value is None or value == '통신장애' for value in [pm10_value, pm10_value_24hr, pm25_value, pm25_value_24hr, o3_value]):
            continue

        if latest_time is None or data_time > latest_time:
            latest_time = data_time
            latest_pm10 = pm10_value
            latest_pm10_24hr = pm10_value_24hr
            latest_pm25 = pm25_value
            latest_pm25_24hr = pm25_value_24hr
            latest_o3 = o3_value

    return {
        'latest_pm10': latest_pm10,
        'latest_pm10_24hr': latest_pm10_24hr,
        'latest_pm25': latest_pm25,
        'latest_pm25_24hr': latest_pm25_24hr,
        'latest_o3': latest_o3,
        'latest_time': latest_time
    }

# Main execution
if __name__ == "__main__":
    # Get yesterday's forecast
    yesterday_forecast = get_yesterday_forecast()

    # Get real-time air quality data
    realtime_air_quality = get_realtime_air_quality()

    # Combine data into a single dictionary
    air_quality_data = {
        **yesterday_forecast,
        **realtime_air_quality
    }

    # Save the data to a JSON file
    with open('data.json', 'w') as f:
        json.dump(air_quality_data, f, ensure_ascii=False, indent=4)
