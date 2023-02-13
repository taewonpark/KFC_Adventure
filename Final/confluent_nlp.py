import sys 
import re
import time
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from datetime import datetime
import os
# from google.cloud import language_v1
import six
import ccloud_lib
from confluent_kafka import Consumer, Producer
import torch
# from datasets import load_dataset
# from transformers import AutoTokenizer
from transformers import AutoModelForSequenceClassification
# from transformers import Trainer, TrainingArguments
from sklearn.metrics import accuracy_score, f1_score
from simplet5 import SimpleT5

from transformers import TokenClassificationPipeline, AutoModelForTokenClassification, AutoTokenizer
from transformers.pipelines import AggregationStrategy

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/Users/jyk/.ssh/tchang3_speech_to_text.json"
if torch.cuda.is_available():       
    device = torch.device("cuda")
    print(f'There are {torch.cuda.device_count()} GPU(s) available.')
    print('Device name:', torch.cuda.get_device_name(0))
else:
    print('No GPU available, using the CPU instead.')
    device = torch.device("cpu")

class KeyphraseExtractionPipeline(TokenClassificationPipeline):
    def __init__(self, model, *args, **kwargs):
        super().__init__(
            model=AutoModelForTokenClassification.from_pretrained(model),
            tokenizer=AutoTokenizer.from_pretrained(model),
            *args,
            **kwargs
        )

    def postprocess(self, model_outputs):
        results = super().postprocess(
            model_outputs=model_outputs,
            aggregation_strategy=AggregationStrategy.SIMPLE,
        )
        return np.unique([result.get("word").strip() for result in results])

class Kafka:
    def __init__(self):
        # Setup Confluent
        config_file = "python.config"

        # Create Consumer instance
        conf = ccloud_lib.read_ccloud_config(config_file)
        consumer_topic = 'text_topic'
        consumer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
        consumer_conf['group.id'] = 'server'
        consumer_conf['auto.offset.reset'] = 'earliest'
        self.consumer = Consumer(consumer_conf)
        # Subscribe to topic
        self.consumer.subscribe([consumer_topic])

        # Create Producer instance
        conf = ccloud_lib.read_ccloud_config(config_file)
        self.producer_topic = 'nlp_topic'
        producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
        self.producer = Producer(producer_conf)
        ccloud_lib.create_topic(conf, self.producer_topic)

class EmotionModel:
    def __init__(self, model_type):
        self.tokenizer = None
        self.model_type = model_type
        if self.model_type == "bert":        
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            ckpt_model = "../model/checkpoint-1250/"
            print("ckpt_model: ", ckpt_model)
            self.model = (AutoModelForSequenceClassification.from_pretrained(ckpt_model, num_labels=6).to(device))
            self.model.eval()
        elif self.model_type == "t5":
            outdir = "../model"
            self.model = SimpleT5()
            mdlist = os.listdir(outdir)
            p = re.compile("(?<=val-loss-).+")
            val_loss_list = list(map(lambda x: float(p.findall(x)[0]), mdlist))
            min_val_loss_model = mdlist[np.argmin(val_loss_list)]
            print('min_val_loss_model: ', min_val_loss_model)
            self.model.load_model("t5", os.path.join(outdir, min_val_loss_model), use_gpu=True)

def load_keyword_extractor():
    # Load Keyphrase Extraction Pipeline
    model_name = "ml6team/keyphrase-extraction-kbir-inspec"
    extractor = KeyphraseExtractionPipeline(model=model_name)
    return extractor

def analyze_emotion(model, content):
    if isinstance(content, six.binary_type):
        content = content.decode("utf-8")
    print('Received text: ', content)
    
    preds_output = model.predict(content)[0]
    print('Emotion: ', preds_output)
    return preds_output

def run_kafka(keyword_extractor):
    my_kafka = Kafka()
    my_model = EmotionModel("bert")
    
    total_count = 0
    nlp_result = {'emotion':None, 'keywords':None}
    try:
        while True:
            msg = my_kafka.consumer.poll(1.0)
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
                if isinstance(sentence, six.binary_type):
                    sentence = sentence.decode("utf-8")
                print('Received text: ', sentence)
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                if my_model.model_type == "bert":
                    sentence_tokenized = my_model.tokenizer(sentence, return_tensors="pt").to(device)
                    output = my_model.model(**sentence_tokenized)
                    nlp_result['emotion'] = torch.argmax(output.logits[0]).item()
                elif my_model.model_type == "t5":
                    nlp_result['emotion'] = my_model.model.predict(sentence)[0]
                nlp_result['keywords'] = keyword_extractor(sentence).tolist()
                print("Emotion: ", nlp_result['emotion'])
                print("Keywords: ", nlp_result['keywords'])

                # produce 
                print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                json_result = json.dumps(nlp_result)
                my_kafka.producer.produce(my_kafka.producer_topic, value=json_result)
                # my_kafka.producer.produce(my_kafka.producer_topic, value=bytes(json_result, 'utf-8'))
                my_kafka.producer.flush()

    except KeyboardInterrupt:
        pass
    finally:
        # Leave group and commit final offsets
        my_kafka.consumer.close()
        
if __name__=="__main__":
    # emotion_model = load_t5_emotion_model()
    keyword_extractor = load_keyword_extractor()
    # print(dir(emotion_model))
    
#     sentence = "Here is where Artificial Intelligence comes in. Currently, classical machine learning methods, that use statistical and linguistic features, are widely used for the extraction process."
    
#     start = time.time()
#     sentence_tokenized = tokenizer(sentence, return_tensors="pt").to(device)
#     # sentence_tokenized = tokenizer(sentence, padding=True, truncation=True)
#     # input_ids = torch.tensor([input_ids_list], dtype=torch.long).to(device)
#     # print(dir(sentence_tokenized))
#     # sentence_tokenized.set_format("torch", columns=["input_ids", "attention_mask"])

#     emotion = emotion_model(**sentence_tokenized)
#     print("Emotion: ", emotion)
#     print(f"Elasped {time.time() - start}")
    
#     start = time.time()    
#     keyphrases = keyword_extractor(sentence)
#     print("Keyphrases: ", keyphrases)
#     print(f"Elasped {time.time() - start}")
    
    run_kafka(keyword_extractor)
    