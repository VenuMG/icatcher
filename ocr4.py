import cv2
import pytesseract
from pytesseract import Output
import imutils
import time
from datetime import datetime

class OCR3:
    def __init__(self, camera_id=0, confidence_threshold=60):
        self.cap = cv2.VideoCapture(camera_id)
        if not self.cap.isOpened():
            raise ValueError(f"Camera {camera_id} not accessible")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        self.confidence_threshold = confidence_threshold
        self.target_words = ["one", "two", "three", "four", "five"]
        self.last_detected_words = []
        self.last_print_time = time.time()
        print("[OCR3] Initialized", flush=True)

    def add_branding(self, frame, text="Code Depot", position=(50, 50), font_scale=1, font_thickness=2, text_color=(255, 255, 255), bg_color=(0, 0, 0)):
        overlay = frame.copy()
        alpha = 0.6
        (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness)
        x, y = position
        cv2.rectangle(overlay, (x, y + 10), (x + text_width, y - text_height - 10), bg_color, -1)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, font_thickness)
        return frame

    def detect_text(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(gray, output_type=Output.DICT, config='--psm 6')
        words = []

        for i in range(len(data['text'])):
            try:
                conf = int(float(data['conf'][i]))
                text = data['text'][i].strip().lower()
                if conf > self.confidence_threshold and text in self.target_words:
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    cx, cy = x + w // 2, y + h // 2
                    words.append((text, (x, y, w, h), (cx, cy), conf))
            except (ValueError, TypeError):
                continue

        self.last_detected_words = words

        if words:
            current_time = time.time()
            if current_time - self.last_print_time > 1.0:  # throttle prints
                timestamp = datetime.now().strftime("%H:%M:%S")
                for word in words:
                    text = word[0]
                    conf = word[3]
                    # Print in [COMMAND] format for main system
                    print(f"[COMMAND] {text}", flush=True)
                    # Optional: also print timestamp and confidence
                    print(f"[{timestamp}] DETECTED: '{text}' (confidence: {conf}%)", flush=True)
                self.last_print_time = current_time

        return words

    def draw_detections(self, frame):
        for text, bbox, center, conf in self.last_detected_words:
            x, y, w, h = bbox
            cx, cy = center
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"{text} ({conf}%)"
            frame = cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 6)
            frame = cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)
        return frame

    def run(self):
        print("[OCR3] Starting real-time OCR...", flush=True)
        print("Target words:", self.target_words, flush=True)
        print("Confidence threshold:", self.confidence_threshold, flush=True)
        print("Press 'q' to quit", flush=True)
        print("=" * 50, flush=True)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[OCR3] Failed to grab frame", flush=True)
                break

            frame = imutils.resize(frame, width=800)
            self.detect_text(frame)
            frame = self.draw_detections(frame)
            frame = self.add_branding(frame)

            # Optional: comment out if running headless in main system
            cv2.imshow("OCR3 - Code Depot", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
        print("[OCR3] Stopped", flush=True)

def main():
    ocr = OCR3()
    ocr.run()

if __name__ == "__main__":
    main()