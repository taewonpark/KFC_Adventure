import sys 
import re
import time
import numpy as np
import pandas as pd
from tqdm import tqdm
import os
# from google.cloud import language_v1
import six
import ccloud_lib
from confluent_kafka import Consumer, Producer
import torch
# from datasets import load_dataset
# from transformers import AutoTokenizer
# from transformers import AutoModelForSequenceClassification
# from transformers import Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, f1_score
from simplet5 import SimpleT5


# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/jyk/.ssh/tchang3_speech_to_text.json"

# Setup Confluent
config_file = "python.config"

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
producer_topic = 'emotion_topic'
producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
producer = Producer(producer_conf)
ccloud_lib.create_topic(conf, producer_topic)


outdir = "../emotion/outputs"
model = SimpleT5()
mdlist = os.listdir(outdir)
p = re.compile("(?<=val-loss-).+")
val_loss_list = list(map(lambda x: float(p.findall(x)[0]), mdlist))
min_val_loss_model = mdlist[np.argmin(val_loss_list)]
print('min_val_loss_model: ', min_val_loss_model)
model.load_model("t5", os.path.join(outdir,min_val_loss_model), use_gpu=True)


def analyze_emotion(content):
    if isinstance(content, six.binary_type):
        content = content.decode("utf-8")
    print('Received text: ', content)
    
    preds_output = model.predict(content)[0]
    print('Emotion: ', preds_output)
    return preds_output


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
            from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            # sentence = msg.value.decode('utf-8')

            # sentiment = sample_analyze_sentiment(sentence, k)
            emotion = analyze_emotion(sentence)
            print(emotion)

            # produce 
            from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            producer.produce(producer_topic, value=bytes(emotion, 'utf-8'))
            producer.flush()

except KeyboardInterrupt:
    pass
finally:
    # Leave group and commit final offsets
    consumer.close()