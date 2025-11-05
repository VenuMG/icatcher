# icatcher
An AI-driven 3-DOF robotic arm system using Raspberry Pi that automates attendance marking through voice commands and OCR-based screen detection. It integrates Vosk voice recognition, Tesseract OCR, and inverse kinematics to perform precise, touch-based human–robot collaborative tasks.
# 🤖 iCatcher – AI-Driven Robotic Arm Attendance System

### 📖 Overview  
**iCatcher** is an AI-driven 3-DOF robotic arm system built on a **Raspberry Pi** platform to automate attendance marking through **voice commands** and **OCR-based screen text detection**.  
The robotic arm, equipped with a stylus, interacts directly with touchscreen interfaces to mark attendance, replicating precise human motion.  
It integrates **offline voice recognition (Vosk)**, **Tesseract OCR**, and **inverse kinematics-based motion control** to perform touch-based human–robot collaborative tasks efficiently.

---

### 🎯 Key Features  
- 🎙️ **Offline Voice Recognition:** Uses Vosk for fast, cloud-free speech-to-text processing.  
- 🧠 **Real-Time OCR Detection:** Identifies screen text using Tesseract OCR and OpenCV preprocessing.  
- 🦿 **Inverse Kinematics Control:** Computes joint angles for the 3-DOF robotic arm to reach any calibrated screen point.  
- ⚙️ **Standalone Operation:** Runs completely on Raspberry Pi — no external PC or internet required.  
- 🖥️ **GUI Interface:** Displays real-time OCR output, voice commands, and robotic arm activity.  
- 🤝 **Human–Robot Collaboration:** Integrates AI perception and mechanical actuation for shared tasks.

---

### 🧰 Hardware Components  
- Raspberry Pi 4 Model B (4GB)  
- PCA9685 Servo Driver  
- 3 Servo Motors (Base, Shoulder, Elbow)  
- USB Camera  
- Bluetooth Microphone or EarPods  
- Stylus for touchscreen interaction  

---

### 💻 Software Requirements  
- **Python 3.9+**  
#### 📦 Required Python Libraries  
Install the following dependencies before running the project:  
```bash
pip install vosk opencv-python pytesseract Pillow numpy adafruit-circuitpython-servokit pyqt5
