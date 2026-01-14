import time
import json
import random
import requests # Cần thêm thư viện này vào requirements.txt
from kafka import KafkaProducer

# Cấu hình Kafka
import os

KAFKA_BOOTSTRAP = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

TOPIC_NAME = 'air_quality_data'
API_KEY = "YOUR_OPENWEATHER_API_KEY" # Điền key nếu muốn chạy thật
LOCATIONS = [
    {"name": "Hanoi", "lat": 21.0285, "lon": 105.8542},
    {"name": "HCM", "lat": 10.8231, "lon": 106.6297},
    {"name": "DaNang", "lat": 16.0544, "lon": 108.2022}
]

def get_real_api_data(lat, lon):
    """Hàm gọi API thật (Nếu bạn có Key)"""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error calling API: {e}")
    return None

def generate_mock_data(lat, lon):
    current_time = int(time.time())
    
    # Random chỉ số để test
    pm2_5 = round(random.uniform(0.5, 200.0), 2)
    aqi = 1
    if pm2_5 > 50: aqi = 3
    if pm2_5 > 150: aqi = 5

    return {
        "coord": [lon, lat], # API trả về [lon, lat]
        "list": [
            {
                "dt": current_time,
                "main": {
                    "aqi": aqi
                },
                "components": {
                    "co": round(random.uniform(200, 300), 2),
                    "no": round(random.uniform(0, 1), 5),
                    "no2": round(random.uniform(0.5, 2.0), 2),
                    "o3": round(random.uniform(50, 100), 2),
                    "so2": round(random.uniform(0.5, 5.0), 2),
                    "pm2_5": pm2_5,   # Quan trọng
                    "pm10": round(random.uniform(10, 50), 2),
                    "nh3": round(random.uniform(0.1, 0.5), 2)
                }
            }
        ]
    }

print("Starting Air Quality Producer...")

while True:
    for loc in LOCATIONS:
        # data = get_real_api_data(loc['lat'], loc['lon'])
        data = generate_mock_data(loc['lat'], loc['lon'])  
        
        if data:
            print(f"Sending data for {loc['name']}: AQI={data['list'][0]['main']['aqi']}")
            producer.send(TOPIC_NAME, value=data)
            
    time.sleep(5) # Gửi mỗi 5 giây