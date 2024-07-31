from WhisperLive import BasicWhisperClient
import numpy as np
import pyaudio
import logging
import os
import time
from scipy.io.wavfile import write


test_name = input("test case name: ")


class Client(BasicWhisperClient):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port, "whisper_tiny_ct")
        self.time = time.time()
        self.bool = True
        segments = ""
    def onTranscript(self, segment: dict):
        super().onTranscript(segment)
        if self.bool:
            self.bool = False
            self.time = time.time() - self.time
        print(segment)


client = Client("52.70.153.157",4231)
client.MakeConnectionToServer()
print(client.retrive_token)

audio = []

def bytes_to_float_array(audio_bytes):
    raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
    return raw_data.astype(np.float32) / 32768.0

chunk = 8192
format = pyaudio.paInt16
channels = 1
rate = 16000
record_seconds = 60000
frames = b""
p = pyaudio.PyAudio()


stream = p.open(
            format=format,
            channels=channels,
            rate=rate,
            input=True,
            frames_per_buffer=chunk
        )

frames = []
try:
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk, exception_on_overflow=False)
        audio_array = bytes_to_float_array(data)
        frames.append(np.fromstring(data, dtype=np.int16))
        try:
            client.send_data_chunk(audio_array.tobytes())
        except Exception as e:
            print(e)
            break

except KeyboardInterrupt:
    print(client.SendEOS())

numpydata = np.hstack(frames)
print(len(audio))
os.mkdir(f"samples/{test_name}/")
write(f"samples/{test_name}/{test_name}.wav",rate,numpydata)
report = f"""
segment_time: {client.time}
text: 
"""
with open(f"samples/{test_name}/{test_name}.wav",'w') as file:
    file.write(report)