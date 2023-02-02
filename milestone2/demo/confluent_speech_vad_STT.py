import argparse
import sys
import struct
import wave
from threading import Thread

from kafka import KafkaProducer
import ccloud_lib
import numpy as np
import json

import pvcobra
from pvrecorder import PvRecorder
from confluent_kafka import SerializingProducer, Producer

import os
from google.cloud import speech

# Setup GCP
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/home/pi/GCPkey/tchang3_speech_to_text.json"
speech_client = speech.SpeechClient()


class CobraDemo(Thread):
    """
    Microphone Demo for Cobra voice activity detection engine.
    """

    def __init__(
            self,
            library_path,
            access_key,
            input_device_index=None):
        """
        Constructor.
        :param library_path: Absolute path to Cobra's dynamic library.
        :param access_key AccessKey obtained from Picovoice Console.
        :param output_path: If provided recorded audio will be stored in this location at the end of the run.
        :param input_device_index: Optional argument. If provided, audio is recorded from this input device. Otherwise,
        the default audio input device is used.
        """

        super(CobraDemo, self).__init__()

        self._library_path = library_path
        self._access_key = access_key
        self._input_device_index = input_device_index
        self._frame_length = 512

    def run(self):
        """
         Creates an input audio stream, instantiates an instance of Cobra object, and monitors the audio stream for
         voice activities.
         """

        cobra = None
        recorder = None
        wav_file = None

        try:
            cobra = pvcobra.create(
                library_path=self._library_path, access_key=self._access_key)
            print("Cobra version: %s" % cobra.version)
            recorder = PvRecorder(device_index=self._input_device_index, frame_length=self._frame_length)
            recorder.start()

            wav_data = bytearray()
            stack = 0  # 0.032 ms per 1 stack
            stack_threshold = 50

            print("Listening...")
            while True:
                pcm = recorder.read()

                voice_probability = cobra.process(pcm)

                if voice_probability > 0.8:
                    wav_data.extend(struct.pack("h" * len(pcm), *pcm))
                    stack = 0
                elif voice_probability <= 0.8 and len(wav_data) > 0 and stack > stack_threshold:
                    recorder.stop()
                    from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    
                    # Setup Confluent
                    config_file = "/home/pi/.confluent/python.config"
                    # Create Producer instance
                    conf = ccloud_lib.read_ccloud_config(config_file)
                    producer_topic = 'text_topic'
                    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)
                    # producer_conf['value.serializer'] = ccloud_lib.json_serializer
                    producer = Producer(producer_conf)
                    # Create topic if needed
                    ccloud_lib.create_topic(conf, producer_topic)
                    
                    # list -> bytearray
                    # byte_data_wav = np.array(message['data']).tobytes()
                    byte_data_wav = np.array(wav_data).tobytes()

                    audio_wav = speech.RecognitionAudio(content=byte_data_wav)

                    config_wav = speech.RecognitionConfig(
                        sample_rate_hertz=16000,
                        enable_automatic_punctuation=True,
                        language_code='en-US',
                        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    )

                    response_standard_wav = speech_client.recognize(
                        config=config_wav,
                        audio=audio_wav
                    )

                    print(response_standard_wav)

                    # produce 
                    try : 
                        result = response_standard_wav.results[0].alternatives[0].transcript
                    except: 
                        result = None

                    if result is not None:
                        from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        producer.produce(producer_topic, value=bytes(result, 'utf-8'))
                        print(result)
                        producer.flush()

                    # data_json = {
                    #     'data' : np.frombuffer(wav_data).tolist(),
                    #     'rate': 16000,
                    #     'sampwidth': 2,
                    #     'n_channel': 1
                    # }

                    recorder.start()
                    wav_data = bytearray()
                else:
                    if len(wav_data) > 0:
                        stack += 1

                percentage = voice_probability * 100
                
                bar_length = int((percentage / 10) * 3)
                empty_length = 30 - bar_length
                sys.stdout.write("\r[%3d]|%s%s|" % (
                    percentage, '█' * bar_length, ' ' * empty_length))
                sys.stdout.flush()

        except KeyboardInterrupt:
            print('Stopping ...')
        finally:
            if cobra is not None:
                cobra.delete()

            if wav_file is not None:
                wav_file.close()
            
            if recorder is not None:
                recorder.delete()

    @classmethod
    def show_audio_devices(cls):
        devices = PvRecorder.get_audio_devices()
        for i in range(len(devices)):
            print('index: %d, device name: %s' % (i, devices[i]))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--library_path', help='Absolute path to dynamic library.', default=pvcobra.LIBRARY_PATH)

    parser.add_argument('--access_key',
                        help='AccessKey provided by Picovoice Console (https://console.picovoice.ai/)',
                        default='JRL2ZWlEuptk0rxFFyfyxGDN7Lmwxll/Q7XFeXc6vbVzJvk+PEI7lg==')

    parser.add_argument('--audio_device_index',
                        help='Index of input audio device.', type=int, default=-1)

    parser.add_argument('--show_audio_devices', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices:
        CobraDemo.show_audio_devices()
    else:
        if args.access_key is None:
            print("missing AccessKey")
        else:
            CobraDemo(
                library_path=args.library_path,
                access_key=args.access_key,
                input_device_index=args.audio_device_index).run()


if __name__ == '__main__':
    main()