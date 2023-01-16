from json import dumps
import time
from kafka import KafkaProducer


producer = KafkaProducer(
    bootstrap_servers=['172.26.16.149:9092'],
    acks=0,
    compression_type='gzip',
    value_serializer=lambda x: dumps(x).encode('utf-8'),
    api_version=(2,0,2)
)


start = time.time()

range_num = 100
for i in range(range_num):
    data = {str(i) : 'test'+str(i)}
    producer.send('first_topic', value=data)
    producer.flush()

print('elapsed : ', time.time() - start)
