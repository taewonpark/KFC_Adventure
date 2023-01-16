from tokenize import group
from kafka import KafkaConsumer
from kasa import SmartBulb
import asyncio

bulb = SmartBulb("192.168.1.152")

async def bulbAction(message: str):
    await bulb.update()
    if message == 'green':
        await bulb.set_hsv(120,100,100)
    elif message == 'red':
        await bulb.set_hsv(359,100,100)
    elif message == 'blue':
        await bulb.set_hsv(240,100,100)
    elif message == 'yellow':
        await bulb.set_hsv(60,100,100)
    else:
        await bulb.set_hsv(0,0,100)


consumer = KafkaConsumer(
    #'first_topic',
    'sentiment_topic',
    bootstrap_servers = ['localhost:9092'],
    group_id = 'bulb-app'
    )

for message in consumer:
    message = message.value.decode('utf-8')
    print(message)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(bulbAction(message))
    