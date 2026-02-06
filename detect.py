# Real-time playing card detection using YOLOv8
#
# Install dependencies:
#   pip install ultralytics opencv-python
#

import cv2
from ultralytics import YOLO

def main():
    # Load the trained model
    model = YOLO("playingCards.pt")

    # Open webcam at 30 FPS
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print("Error: Could not open webcam.")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Run inference
        results = model(frame, imgsz=320, verbose=False)

        # Draw detections
        for box in results[0].boxes:
            # Bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Class name and confidence
            cls_id = int(box.cls[0])
            name = model.names[cls_id]
            conf = int(box.conf[0] * 100)
            label = f"{name} ({conf}%)"

            # Draw box and label
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Playing Card Detection", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
