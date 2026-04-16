from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import face_recognition
import numpy as np
import faiss
from io import BytesIO
import cv2
import math

from database import get_db, UserFace, SessionLocal

app = FastAPI()

VECTOR_DIMENSION = 128 
index = faiss.IndexFlatL2(VECTOR_DIMENSION) 
user_ids_map = [] 

@app.on_event("startup")
def load_templates():
    """Loads all MySQL templates into the FAISS memory index."""
    db = SessionLocal()
    users = db.query(UserFace).all()
    for user in users:
        encoding = np.frombuffer(user.face_encoding, dtype=np.float64)
        index.add(np.array([encoding]))
        user_ids_map.append(user.id)
    db.close()
    print(f"Loaded {len(user_ids_map)} templates.")

@app.post("/enroll")
async def enroll_user(name: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Standard REST endpoint for one-time enrollment."""
    file_bytes = await file.read()
    image = face_recognition.load_image_file(BytesIO(file_bytes))
    encodings = face_recognition.face_encodings(image)
    
    if not encodings:
        raise HTTPException(status_code=400, detail="No face detected.")
    
    encoding = encodings[0]
    
    if db.query(UserFace).filter(UserFace.name == name).first():
        raise HTTPException(status_code=400, detail="User already exists.")
    
    db_user = UserFace(name=name, face_encoding=encoding.tobytes())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    index.add(np.array([encoding]))
    user_ids_map.append(db_user.id)
    
    return {"message": f"Successfully enrolled {name}"}

@app.websocket("/ws/authenticate")
async def websocket_authenticate(websocket: WebSocket):
    """Real-time WebSocket endpoint for continuous video matching."""
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            # Receive JPEG frame from client
            bytes_data = await websocket.receive_bytes()
            
            # Decode image
            nparr = np.frombuffer(bytes_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Convert BGR (OpenCV) to RGB (face_recognition)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Detect face locations and extract encodings
            face_locations = face_recognition.face_locations(rgb_img)
            face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
            
            results = []
            if index.ntotal > 0:
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Query FAISS
                    distances, indices = index.search(np.array([face_encoding]), k=1)
                    
                    # FAISS returns squared L2 distance. Convert to standard Euclidean.
                    squared_distance = distances[0][0]
                    true_distance = math.sqrt(squared_distance)
                    
                    # Standard face_recognition tolerance is 0.6. 
                    # 0.45 is very strict to prevent false positives.
                    TOLERANCE = 0.45 
                    
                    if true_distance <= TOLERANCE:
                        matched_id = user_ids_map[indices[0][0]]
                        user = db.query(UserFace).filter(UserFace.id == matched_id).first()
                        name = user.name
                    else:
                        name = "Unknown"
                        
                    results.append({
                        "name": name,
                        "box": {"top": top, "right": right, "bottom": bottom, "left": left}
                    })
            
            # Send matches and box coordinates back to frontend
            await websocket.send_json({"faces": results})
            
    except WebSocketDisconnect:
        print("Client disconnected")
    finally:
        db.close()