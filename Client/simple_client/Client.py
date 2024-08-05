from WhisperLive import BasicWhisperClient
import numpy as np
import pyaudio
import logging


class Client(BasicWhisperClient):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port, "whisper_tiny_ct")
        self.transcribe = ""
        self.counter = 0
    def onTranscript(self, segment: dict):
        super().onTranscript(segment)
        self.transcribe += f"start: {segment.get('start')}, end: {segment.get('end')}, text: {segment.get('text')}\n"
        # print(f"SEGMENT {segment}")
        # if segment[self.counter].get("is_final"):
        #     self.transcribe = f"start: {segment[self.counter].get('start')}, end: {segment[self.counter].get('end')}, text: {segment[self.counter].get('text')}\n"
        #     self.counter+=1

client = Client("52.70.153.157",9001)
client.MakeConnectionToServer()
print(client.retrive_token)


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
try:
    for _ in range(0, int(rate / chunk * record_seconds)):
        data = stream.read(chunk, exception_on_overflow=False)
        audio_array = bytes_to_float_array(data)
        try:
            client.send_data_chunk(audio_array.tobytes())
        except Exception as e:
            print(client.transcribe)
            print(e)
            break

except KeyboardInterrupt:
    print(client.SendEOS())

print(client.transcribe)