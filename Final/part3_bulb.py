import os
import ccloud_lib
from confluent_kafka import Consumer, Producer

import asyncio
from kasa import SmartBulb

import json

ip = "172.26.174.247"

os.system(f"kasa --type bulb --host {ip} hsv 0 0 10")

color_text = {
	0: [196, 80, 90],
	1: [135, 65, 65],
	2: [289, 62, 56], 
	3: [0, 85, 85],
	4: [112, 34, 89],
	5: [52, 55, 98]
}

idx_emotion = {
    'sadness': 0,
    'joy': 1,
    'love': 2,
    'anger': 3,
    'fear': 4,
    'surprise':5
}

# Setup Confluent
config_file = "./python.config"

# Create Consumer instance
conf = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'nlp_topic'
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
consumer_conf['group.id'] = 'server'
consumer_conf['auto.offset.reset'] = 'earliest'
consumer = Consumer(consumer_conf)
# Subscribe to topic
consumer.subscribe([consumer_topic])


# Run with Confluent
try:
    while True:
        msg = consumer.poll(0.1)
        if msg is None:
            continue
        elif msg.error():
            print('error: {}'.format(msg.error()))
        else:
            nlp = msg.value()
            nlp = json.loads(nlp)
            sentiment = nlp['emotion']

            print(sentiment)
            h, s, v = color_text[sentiment]
            os.system(f"kasa --type bulb --host {ip} hsv {h} {s} {v}")
            os.system(f"kasa --type bulb --host {ip} brightness 3")
except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()