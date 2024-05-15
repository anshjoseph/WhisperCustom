import os
import base64
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn
from audioop import ulaw2lin, ratecv
from uuid import uuid4
import numpy as np
import threading
import json
import websocket
import uuid
from queue import Queue
from websockets.exceptions import *
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class ClientConnection:
    def __init__(self,host:str,port:int) -> None:
        self.ws_url =  f"ws://{host}:{port}"
        self.ws_connection:websocket.WebSocket = websocket.WebSocket()
        self.ws_connection.connect(self.ws_url)
        self.client_id:str = str(uuid.uuid4())

        self.retrive_token= None


        self.commited_list:list[str] = []



        self.prev_segment = None
        self.curr_segment = None
        self.seg_ptr = 0
        self.same_data_count = 0


        self.segments_collection_thread:threading.Thread = threading.Thread(target=self.get_segment) 

        self.segments:Queue = Queue()
    def MakeConnectionToServer(self):
        self.ws_connection.send(json.dumps(
            {
                "uid": str(uuid.uuid4()),
                "language": "en",
                "task": "translate",
                "model": "small",
                "use_vad": True
            }
        ))
        self.retrive_token = json.loads(self.ws_connection.recv())
        self.segments_collection_thread.start()
    def __check_server_status(self):
        if self.retrive_token == None:
            return False
        elif self.retrive_token["message"] == "SERVER_READY":
            return True
        return False
    
    def send_data_chunk(self,chunk:bytes):
        self.ws_connection.send(chunk,websocket.ABNF.OPCODE_BINARY)
    

    def CloseConnectionToServer(self):
        self.ws_connection.close()
    
    def SendEOS(self):
        self.ws_connection.send(b'END_OF_AUDIO',websocket.ABNF.OPCODE_BINARY)
        return self.ws_connection.recv()
    
    def SendEnd(self):
        self.SendEOS()
        self.CloseConnectionToServer()
    
    def AddComited(self, segments):
        if len(segments) > 1 and len(segments) - self.seg_ptr >= 2:
            self.commited_list.append(segments[self.seg_ptr]['text'])
            segments[self.seg_ptr]["is_final"] = True
            self.seg_ptr += 1
        return segments
        # else:
        #     if self.prev_segment[-1]["end"] == segments[-1]["end"] and self.prev_segment[-1]["hash"] == segments[-1]["hash"]:
        #         self.same_data_count += 1
        #         if self.same_data_count > 6:
        #             segments[self.seg_ptr+1]["is_final"] = True

            

    def AddAttributes(self,segments:dict):
        segments_list = [seg for seg in segments['segments']]

        # for 

        for i,seg in enumerate(segments_list):
            if seg['text'] in self.commited_list:
                seg["is_final"] = True
            else:
                seg["is_final"] = False
        return segments_list


        
    
    def get_segment(self):
        while True:
            try:
                data:dict = json.loads(self.ws_connection.recv())
                if "message" not in data:
                    # self.segments.put(data)
                    data = self.AddAttributes(data)
                    
                    data = self.AddComited(data)

                    if self.curr_segment == None:
                        self.curr_segment = data
                    else:
                        self.prev_segment = self.curr_segment
                        self.curr_segment = data
                    print(data)
                else:
                    print(data)
                    if data['message'] == 'DISCONNECT':
                        self.ws_connection.close()
                        break
                    elif data['message'] == "UTTERANCE_END":
                        self.prev_segment[-1]['is_final'] = True
                        print(self.prev_segment)
                    elif data['message'] == 'SERVER_READY':
                        print("server id ready")
                    

            except:
                break 


client = ClientConnection("127.0.0.1",9090)
client.MakeConnectionToServer()
print(client.retrive_token)

def bytes_to_float_array(audio_bytes):
    raw_data = np.frombuffer(buffer=audio_bytes, dtype=np.int16)
    return raw_data.astype(np.float32) / 32768.0

frames:bytes = b''


@app.websocket("/connection")
async def websocket_endpoint(websocket: WebSocket):
    global frames
    await websocket.accept()
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
            audio_chunk = bytes_to_float_array(audio_chunk).tobytes()
            if len(frames) >= 120*70:
                print("sent frame")
                client.send_data_chunk(frames)
                frames = b''
            else:
                print(len(frames),end='\r')
                frames += audio_chunk
if __name__ == "__main__":
    print(os.getenv('REDIS_URL'))
    uvicorn.run('quickstart_server:app',port=5001,reload=True)