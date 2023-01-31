import os
import ccloud_lib
from confluent_kafka import Consumer, Producer

# Setup Confluent
config_file = "/Users/jyk/.confluent/python.config"

# Create Consumer instance
conf = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'sentiment_topic'
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
            sentiment = msg.value()
            print(sentiment)

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()