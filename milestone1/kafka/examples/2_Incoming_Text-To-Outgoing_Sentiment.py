from tokenize import group
from kafka import KafkaConsumer
from kafka import KafkaProducer

from re import X
import nltk
# from nltk.sentiment.vader import SentimentIntensityAnalyzer

consumer = KafkaConsumer(
    'first_topic',
    bootstrap_servers = ['172.26.16.149:9092'], 
    group_id = 'NLP-app',
    api_version=(2,0,2)
    )

producer = KafkaProducer(
    bootstrap_servers=['172.26.16.149:9092'],
    api_version=(2,0,2)
)

# sent_analyzer = SentimentIntensityAnalyzer()

for message in consumer:
    incoming = message.value.decode('utf-8')
    print(incoming)

    # label = sent_analyzer.polarity_scores(incoming)
    # # keys can be neg, neu, pos, and compound
    # max_key = max(label, key=label.get)

    # print(max_key)

    # if max_key == 'pos':
    #     outgoing = 'green'
    # elif max_key == 'neg':
    #     outgoing = 'red'
    # elif max_key == 'neu':
    #     outgoing = 'yellow'
    # else: outgoing = 'blue'

    # producer.send('sentiment_topic',
    #     key=b'commands', 
    #     value=bytes(outgoing, 'utf-8')
    # )
    # producer.flush()




