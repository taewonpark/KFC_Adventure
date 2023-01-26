from kafka import KafkaConsumer
from gtts import gTTS
import os

language = 'en'
output_mp3_file = "temp.mp3"
output_wav_file = "temp.wav"

consumer = KafkaConsumer(
    'text_topic',
    bootstrap_servers = ['localhost:9092'],
    api_version=(2,0,2)
    )

for text in consumer:
    text = text.value.decode('utf-8')
    print(text)

    # os.system("gtts-cli {text} | play -t mp3 -")

    mp3_obj = gTTS(text=text, lang=language, slow=False)
    mp3_obj.save(output_mp3_file)

    os.system(f"ffmpeg -y -i {output_mp3_file} -ac 1 -f wav {output_wav_file}")
    os.system(f"aplay {output_wav_file}")