from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import time
import uvicorn
from dotenv import load_dotenv
import os

# python3.11 gb_websocket.py

app = FastAPI()
load_dotenv()

class ConnectionManager:
  def __init__(self):
    self.activate_connections:List[WebSocket] = []

  async def connect(self, websocket:WebSocket):
    await websocket.accept()
    self.activate_connections.append(websocket)
    client_address = websocket.client
    # print("=== connecting!! ===", time.strftime('%Y-%m-%d %H:%M:%S'))
    print(f"=== connecting!! === {client_address}")

  async def disconnect(self, websocket: WebSocket):
    if websocket in self.activate_connections:
      try:
        await websocket.close(code=1000, reason="Normal closure")
      except Exception as e:
        print(f"=== Error during WebSocket close === : {e}")
      finally:
        self.activate_connections.remove(websocket)

  async def send_data_to_all(self, data:str, sender:WebSocket = None):
    disconnected_ws = []
    for connection in self.activate_connections:
      if connection != sender:
        try:
          await connection.send_json(data)

          # db 저장 코드 작성 예정

        except Exception as e:
          print(f'=== Error sending data === : {e}')
          disconnected_ws.append(connection)

    for ws in disconnected_ws:
      await self.disconnect(ws)

manager = ConnectionManager()

@app.websocket("/greenBlock/ws")
async def websocket_endpoint(websocket:WebSocket):
  try:
    await manager.connect(websocket)
    while True:
      data = await websocket.receive_json()
      # print(f'recv_data: {data}')

      await manager.send_data_to_all(data)
  except WebSocketDisconnect:
    print(f'=== Client disconnected === : {websocket.client}')
    await manager.disconnect(websocket)
  except Exception as e:
    print(f'=== Error occurred === : {e}')
    await manager.disconnect(websocket)

if __name__ == "__main__":
  HOST = os.getenv('HOST')
  PORT = int(os.getenv('PORT'))
  uvicorn.run(app, host=HOST, port=PORT)
