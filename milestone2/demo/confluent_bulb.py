import os
import ccloud_lib
from confluent_kafka import Consumer, Producer

import asyncio
from kasa import SmartBulb

import os

ip = "172.26.174.247"

"""
# connect to bulb
bulb = SmartBulb("172.26.174.247")
asyncio.run(bulb.update())

async def set_hsv(h, s, v):
    await bulb.set_hsv(h, s, v)

async def set_brightness(m):
    await bulb.set_brightness(m)

asyncio.run(set_brightness(3))
print('a')
asyncio.run(set_hsv(0, 0, 100))
"""

# os.system(f"kasa --type bulb --host {ip} hsv 0 0 100 | kasa --type bulb --host {ip} brightness 3")
os.system(f"kasa --type bulb --host {ip} hsv 0 0 100")

# for h, s, v in color_text.values():
#     time.sleep(1)
#     os.system(f"kasa --type bulb --host {ip} hsv {h} {s} {v}")

color_text = {
	'sadness': [196, 80, 90],
	'joy': [135, 65, 65],
	'love': [289, 62, 56], #[346, 96, 93],
	'anger': [0, 85, 85],
	'fear': [112, 34, 89],
	'surprise': [52, 55, 98]
}

# Setup Confluent
config_file = "/home/pi/.confluent/python.config"

# Create Consumer instance
conf = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'emotion_topic'
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
consumer_conf['group.id'] = 'server'
consumer_conf['auto.offset.reset'] = 'earliest'
consumer = Consumer(consumer_conf)
# Subscribe to topic
consumer.subscribe([consumer_topic])


# Run with Confluent
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
            sentiment = msg.value().decode()
            from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            print(sentiment)
            h, s, v = color_text[sentiment]
            # os.system(f"kasa --type bulb --host {ip} brightness 2 | kasa --type bulb --host {ip} hsv {h} {s} {v}")
            os.system(f"kasa --type bulb --host {ip} hsv {h} {s} {v}")
            # os.system(f"kasa --type bulb --host {ip} brightness 1")
            # asyncio.run(set_hsv(*color_idx[sentiment]))

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()