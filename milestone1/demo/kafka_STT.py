import os
from google.cloud import speech
from kafka import KafkaConsumer
from kafka import KafkaProducer
import numpy as np
import json


# Setup GCP
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/jyk/.ssh/tchang3_speech_to_text.json"
speech_client = speech.SpeechClient()

# Setup Kafka
consumer = KafkaConsumer(
    'speech_topic',
    bootstrap_servers = ['172.26.53.200:9092'], 
    group_id = 'server',
    api_version=(2,0,2),
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)
producer = KafkaProducer(
    bootstrap_servers=['172.26.53.200:9092'],
    api_version=(2,0,2)
)

# Run with Kafka
for message in consumer:
    message = message.value
    print(message['data'])
    # break

    # list -> bytearray
    byte_data_wav = np.array(message['data']).tobytes()

    audio_wav = speech.RecognitionAudio(content=byte_data_wav)

    config_wav = speech.RecognitionConfig(
        sample_rate_hertz=16000,
        enable_automatic_punctuation=True,
        language_code='en-US',
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    )

    response_standard_wav = speech_client.recognize(
        config=config_wav,
        audio=audio_wav
    )

    print(response_standard_wav)

    # produce 
    print("producer sends test messages")

    producer.send('text_topic', value=bytes(response_standard_wav.results[0].alternatives[0].transcript, 'utf-8'))
    producer.flush()