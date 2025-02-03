from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import uvicorn
from dotenv import load_dotenv
import os
import logging

# python3.11 gb_websocket.py

app = FastAPI()
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
  def __init__(self):
    self.activate_connections:List[WebSocket] = []

  async def connect(self, websocket:WebSocket):
    await websocket.accept()
    self.activate_connections.append(websocket)
    client_address = websocket.client
    logger.info(f"=== connecting!! === {client_address}")

  async def disconnect(self, websocket: WebSocket):
    if websocket in self.activate_connections:
      try:
        await websocket.close(code=1000, reason="Normal closure")
      except RuntimeError as e:
        logger.info(f"=== WebSocket already closed === : {e}")
      except Exception as e:
        logger.error(f"=== Error during WebSocket close === : {e}")
      finally:
        self.activate_connections.remove(websocket)

  async def send_data_to_all(self, data:str, sender:WebSocket = None):
    disconnected_ws = []
    for connection in self.activate_connections:
      if connection != sender:
        try:
          # logger.info(f"connection: {connection}")
          # logger.info(f"sender: {sender}")
          await connection.send_json(data)

        except Exception as e:
          logger.error(f'=== Error sending data === : {e}')
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
      # logger.info(f'recv_data: {data}')

      await manager.send_data_to_all(data, sender=websocket)
  except WebSocketDisconnect:
    logger.info(f'=== Client disconnected === : {websocket.client}')
  except Exception as e:
    logger.error(f'=== Error occurred === : {e}')
  finally:
    await manager.disconnect(websocket)

if __name__ == "__main__":
  HOST = os.getenv('HOST')
  PORT = int(os.getenv('PORT'))
  uvicorn.run(app, host=HOST, port=PORT)
