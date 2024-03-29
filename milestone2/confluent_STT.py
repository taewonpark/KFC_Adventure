import os
from google.cloud import speech
import numpy as np
import ccloud_lib
from confluent_kafka import DeserializingConsumer, Producer

# Setup GCP
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/jyk/.ssh/tchang3_speech_to_text.json"
speech_client = speech.SpeechClient()

# Setup Confluent
config_file = "/Users/jyk/.confluent/python.config"

# Create Consumer instance
conf = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'speech_topic'
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
consumer_conf['group.id'] = 'server'
consumer_conf['auto.offset.reset'] = 'earliest'
consumer_conf['value.deserializer'] = ccloud_lib.json_deserializer
consumer = DeserializingConsumer(consumer_conf)
# Subscribe to topic
consumer.subscribe([consumer_topic])

# Create Producer instance
conf = ccloud_lib.read_ccloud_config(config_file)
producer_topic = 'text_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
# producer_conf['value.serializer'] = ccloud_lib.json_serializer
producer = Producer(producer_conf)
# Create topic if needed
ccloud_lib.create_topic(conf, producer_topic)


# Run with Confluent
total_count = 0
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            # No message available within timeout.
            # Initial message consumption may take up to
            # `session.timeout.ms` for the consumer group to
            # rebalance and start consuming
            # print("Waiting for message or event/error in poll()")
            continue
        elif msg.error():
            print('error: {}'.format(msg.error()))
        else:
            message = msg.value()
            print(message)

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
            producer.produce(producer_topic, value=bytes(response_standard_wav.results[0].alternatives[0].transcript, 'utf-8'))
            print(response_standard_wav.results[0].alternatives[0].transcript)
            producer.flush()

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()
