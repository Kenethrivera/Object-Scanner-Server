from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import cv2
import numpy as np
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# YOLOv8 classification model (e.g., best.pt trained with yolov8n-cls.yaml)
model = YOLO('best_latest.pt')

CONFIDENCE_THRESHOLD = 0.80  

@app.post("/analyze-frame")
async def analyze_frame(image: UploadFile = File(...)):
    contents = await image.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if frame is None:
        return {"status": "failed", "message": "Corrupted image"}

    cv2.imwrite("/tmp/debug_received.jpg", frame)
    print("\n--- NEW SCAN RECEIVED ---")

    results = model(frame, verbose=False)

    detected_item = None
    highest_confidence = 0.0

    for result in results:
        if result.probs is not None:
            top1_index = result.probs.top1          # index of top predicted class
            top1_conf = result.probs.top1conf.item() # confidence of top class
            class_name = model.names[top1_index].lower()

            print(f"AI classified: {class_name} (Confidence: {top1_conf:.2f})")

            if top1_conf > CONFIDENCE_THRESHOLD and top1_conf > highest_confidence:
                highest_confidence = top1_conf
                detected_item = class_name


    if detected_item:
        print(f"SUCCESS: Sending '{detected_item}' back to Flutter.")
        return {"status": "success", "item": detected_item}
    else:
        print("FAILED: Nothing matched the threshold.")
        return {"status": "failed", "message": "No valid tool recognized"}
    
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)