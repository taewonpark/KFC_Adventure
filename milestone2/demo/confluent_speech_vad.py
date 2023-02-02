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
from confluent_kafka import SerializingProducer


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
                    # Setup Confluent Producer
                    config_file = "/home/pi/.confluent/python.config"
                    topic = "speech_topic"
                    conf = ccloud_lib.read_ccloud_config(config_file)
                    # Create topic if needed
                    ccloud_lib.create_topic(conf, topic)
                    producer_conf = ccloud_lib.pop_schema_registry_params_from_config(conf)

                    producer_conf['value.serializer'] = ccloud_lib.json_serializer

                    producer = SerializingProducer(producer_conf)

                    data_json = {
                        'data' : np.frombuffer(wav_data).tolist(),
                        'rate': 16000,
                        'sampwidth': 2,
                        'n_channel': 1
                    }
                    from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    # output 보내기
                    producer.produce(topic, key=b'wav', value=data_json)
                    producer.flush()

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