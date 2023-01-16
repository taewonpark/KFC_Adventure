from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'first_topic',
    bootstrap_servers = ['172.26.16.149:9092'], 
    group_id = 'server',
    api_version=(2,0,2)
    )

for message in consumer:
    message = message.value.decode('utf-8')
    print(message)