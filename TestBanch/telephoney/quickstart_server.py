import os
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from audioop import ulaw2lin, ratecv
import numpy as np
from uuid import uuid4
from WhisperLive import BasicWhisperClient
import wave
import time
load_dotenv()

app = FastAPI()


class Client(BasicWhisperClient):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port, "6e816d54-31b2-47de-93ca-4bc1dd17b77c")
        self.transcribe = "" 
    def onTranscript(self, segment: dict):
        super().onTranscript(segment)
        self.transcribe += f"start: {segment.get('start')}, end: {segment.get('end')}, text: {segment.get('text')}\n"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def bytes_to_float_array(audio_bytes):
    raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
    return raw_data.astype(np.float32) / 32768.0
def numpy_audioop_helper(x, xdtype, func, width, ydtype):
    '''helper function for using audioop buffer conversion in numpy'''
    xi = np.frombuffer(x,dtype=xdtype)
    y = np.frombuffer(func(xi.tobytes(), width), dtype=ydtype)
    return y.reshape(xi.shape)

@app.websocket("/connection")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    __ = time.time()
    client = Client("52.70.153.157",9001)
    client.MakeConnectionToServer()
    print(client.retrive_token)
    print(f"WEBSOCKET TIME: {time.time()- __}")
    
    audio = []
    try:
        while True:
            data = await websocket.receive_json()
            if data['event'] == "connected":
                print("CALL CONNECTED")
            elif data['event'] == "start":
                print("CALL STARTED")
            elif data['event'] == "media":
                audio_chunk = base64.b64decode(data['media']['payload'])
                # print(len(audio_chunk))
                audio_chunk = ulaw2lin(audio_chunk, 2)
                audio_chunk = ratecv(audio_chunk, 2, 1, 8000, 16000, None)[0]
                # print(audio_chunk)
                for i in bytes_to_float_array(audio_chunk):
                    audio.append(i)
                if len(audio) > 8000:
                    client.send_data_chunk(np.asarray(audio).tobytes())
                    audio.clear()
        
        
    except Exception as e:
        print(f"TIME: {client._time}")
        print("++++++++++++++++++++++++++++++++++++++")
        print(client.transcribe)
        client.SendEOS()
if __name__ == "__main__":
    uvicorn.run('quickstart_server:app',port=5001,reload=True)