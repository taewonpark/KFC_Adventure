import os
from google.cloud import language_v1
import six
import ccloud_lib
from confluent_kafka import Consumer, Producer

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/jyk/.ssh/tchang3_speech_to_text.json"

# Setup Confluent
config_file = "/Users/jyk/.confluent/python.config"


# Create Consumer instance
conf = ccloud_lib.read_ccloud_config(config_file)
consumer_topic = 'text_topic'
consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
consumer_conf['group.id'] = 'server'
consumer_conf['auto.offset.reset'] = 'earliest'
consumer = Consumer(consumer_conf)
# Subscribe to topic
consumer.subscribe([consumer_topic])

# Create Producer instance
conf = ccloud_lib.read_ccloud_config(config_file)
producer_topic = 'sentiment_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
producer = Producer(producer_conf)
ccloud_lib.create_topic(conf, producer_topic)

def sample_analyze_sentiment(content, critical_value):

    client = language_v1.LanguageServiceClient()

    # content = 'Your text to analyze, e.g. Hello, world!'

    if isinstance(content, six.binary_type):
        content = content.decode("utf-8")

    type_ = language_v1.Document.Type.PLAIN_TEXT
    document = {"type_": type_, "content": content}

    response = client.analyze_sentiment(request={"document": document})
    sentiment = response.document_sentiment

    score = sentiment.score
    mag = sentiment.magnitude
    print("Score: {}".format(sentiment.score))
    print("Magnitude: {}".format(sentiment.magnitude))

    if score > critical_value :
        result = "positive"
    elif score < (-1.0 * critical_value) :
        result = "negative"
    else :
        result = "neutral_or_mixed"
    
    return result

k = 0.25   # critical value

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
            sentence = msg.value()
            print('sentence', sentence)

            sentiment = sample_analyze_sentiment(sentence, k)
            print(sentiment)

            # produce 
            producer.produce(producer_topic, value=bytes(sentiment, 'utf-8'))
            producer.flush()

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()