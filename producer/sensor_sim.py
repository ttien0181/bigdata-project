import time
import json
import random
import requests # Cần thêm thư viện này vào requirements.txt
from kafka import KafkaProducer

# Cấu hình Kafka
import os

KAFKA_BOOTSTRAP = os.environ.get('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
print(f"Connecting to Kafka at {KAFKA_BOOTSTRAP}...")

try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    print("Kafka producer initialized successfully!")
except Exception as e:
    print(f"Failed to initialize Kafka producer: {e}")
    raise

TOPIC_NAME = 'weather_data'
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
    
    # Random nhiệt độ và độ ẩm theo vị trí
    # Hanoi: 15-35°C, Humidity: 60-90%
    # HCM: 25-38°C, Humidity: 65-95%
    # DaNang: 20-36°C, Humidity: 60-85%
    
    if 20.9 <= lat <= 21.2:  # Hanoi
        temp = round(random.uniform(15.0, 35.0), 2)
        humidity = random.randint(60, 90)
        feels_like = round(temp + random.uniform(-2, 2), 2)
    elif 10.7 <= lat <= 11.0:  # HCM
        temp = round(random.uniform(25.0, 38.0), 2)
        humidity = random.randint(65, 95)
        feels_like = round(temp + random.uniform(-1, 3), 2)
    else:  # DaNang
        temp = round(random.uniform(20.0, 36.0), 2)
        humidity = random.randint(60, 85)
        feels_like = round(temp + random.uniform(-2, 2), 2)
    
    pressure = random.randint(1000, 1020)

    return {
        "coord": [lon, lat], # API trả về [lon, lat]
        "list": [
            {
                "dt": current_time,
                "main": {
                    "temp": temp,
                    "feels_like": feels_like,
                    "humidity": humidity,
                    "pressure": pressure
                }
            }
        ]
    }

print("Starting Weather Data Producer...")

while True:
    try:
        for loc in LOCATIONS:
            # data = get_real_api_data(loc['lat'], loc['lon'])
            data = generate_mock_data(loc['lat'], loc['lon'])  
            
            if data:
                temp = data['list'][0]['main']['temp']
                humidity = data['list'][0]['main']['humidity']
                print(f"Sending data for {loc['name']}: Temp={temp}°C, Humidity={humidity}%")
                producer.send(TOPIC_NAME, value=data)
        
        producer.flush()  # Ensure messages are sent
        time.sleep(5) # Gửi mỗi 5 giây
    except Exception as e:
        print(f"Error in main loop: {e}")
        time.sleep(5)