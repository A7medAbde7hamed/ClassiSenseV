# 🎯 Real-Time Person Tracker with Interactive ROI

A real-time computer vision application that detects, tracks, and counts people within a user-defined Region of Interest (ROI), built with **YOLO11** and **OpenCV**.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![YOLO](https://img.shields.io/badge/YOLO-v11-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ Features

- 🖱️ **Interactive ROI Selection** — Draw any zone on the video using mouse click-and-drag
- 👥 **Person Detection** — Powered by the state-of-the-art YOLO11 model
- 🔗 **Persistent Multi-Object Tracking** — Unique IDs maintained across frames using ByteTrack
- 🎯 **Zone-Based Filtering** — Only counts people whose center-point lies inside the ROI
- 📊 **Live Analytics Overlay** — Real-time total person count displayed on screen
- ⌨️ **Playback Controls** — Spacebar to pause/resume, `Q` to quit
- 🎨 **Visual Feedback** — Bounding boxes, tracking IDs, and center-point markers

---

## 🚀 Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.10+** | Core language |
| **Ultralytics YOLO11** | Object detection & tracking |
| **OpenCV** | Video processing & GUI |
| **NumPy** | Array operations |

---

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/NosaybaManjoudAli/yolo-person-tracker.git
cd yolo-person-tracker
```

### 2. (Optional) Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### 1. Prepare your video

Place your input video in the project folder and name it `video.mp4`  
*(or update the path in `tracker.py` to match your file).*

### 2. Run the script

```bash
python tracker.py
```

### 3. Interact with the window

| Action | Result |
|--------|--------|
| 🖱️ **Click & drag** | Draw a Region of Interest |
| ⌨️ **Spacebar** | Pause / resume the video |
| ⌨️ **Q** | Quit the application |

### 4. Watch the magic ✨

- People detected inside your ROI will be highlighted with green boxes
- Each person gets a persistent tracking ID
- Total person count updates live at the top of the screen

---

## 🧠 How It Works

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Video Frame │ ──▶ │  YOLO11      │ ──▶ │  ByteTrack   │
│              │     │  Detection   │     │  (IDs)       │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
                     ┌──────────────┐     ┌──────────────┐
                     │  Render &    │ ◀── │  ROI Filter  │
                     │  Display     │     │  (Centroid)  │
                     └──────────────┘     └──────────────┘
```

1. **Detection** — Every frame is passed through YOLO11 to locate objects
2. **Tracking** — ByteTrack assigns a persistent ID to each detected person
3. **Filtering** — The centroid of each bounding box is checked against the ROI coordinates
4. **Visualization** — Matching detections are drawn with boxes, IDs, and center points
5. **Counting** — Total persons in the ROI are displayed live on the frame

---

## 📁 Project Structure

```
yolo-person-tracker/
├── tracker.py           # Main application script
├── requirements.txt     # Python dependencies
├── README.md            # Project documentation
├── .gitignore           # Git exclusions
└── video.mp4            # Your input video (example included)
```

---

## ⚙️ Configuration

You can customize the behavior by editing these variables in `tracker.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `TARGET_CLASS` | `0` | COCO class ID (0 = person) |
| `model` | `yolo11n.pt` | YOLO model weights (nano variant) |
| `video_source` | `"video.mp4"` | Input video path or webcam index (e.g., `0`) |

### Use your webcam instead:

```python
cap = cv2.VideoCapture(0)   # 0 = default webcam
```

### Use a different YOLO variant (better accuracy, slower):

```python
model = YOLO("yolo11s.pt")   # small
model = YOLO("yolo11m.pt")   # medium
model = YOLO("yolo11l.pt")   # large
```

---

## 🎯 Use Cases

- 🏪 **Retail Analytics** — Count customers in specific store zones
- 🚶 **Crowd Monitoring** — Measure occupancy in waiting areas
- 🏢 **Office Safety** — Track people in restricted zones
- 🎓 **Classroom Attendance** — Auto-count students in a room
- 🚇 **Transit Monitoring** — Analyze platform crowding

---

## 🚧 Roadmap / Future Improvements

- [ ] Support for **multiple simultaneous ROIs**
- [ ] **Dwell time** calculation (how long each person stays in the ROI)
- [ ] **Entry/Exit event logging** to CSV with timestamps
- [ ] **Web dashboard** with live stats (Flask/Streamlit)
- [ ] **Heatmap generation** showing high-traffic areas
- [ ] **Edge deployment** on Jetson / Raspberry Pi

---

## 🧩 Requirements

See `requirements.txt`:

```
ultralytics
opencv-python
numpy
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: ultralytics` | Run `pip install ultralytics` |
| Video window not opening | Make sure `video.mp4` exists in the project folder |
| Low FPS / laggy | Use a smaller model (`yolo11n.pt`) or resize frames |
| Mouse callback not working | Ensure `cv2.namedWindow()` is called before `cv2.setMouseCallback()` |

---

## 📚 What I Learned

- Real-time video processing pipelines with OpenCV
- Integrating pre-trained deep learning models (YOLO11) into applications
- Multi-object tracking using ByteTrack with persistent IDs
- Interactive UI design with OpenCV mouse callbacks
- Coordinate geometry for point-in-rectangle filtering
- Building end-to-end computer vision projects from scratch

---

## 📝 License

This project is licensed under the **MIT License** — feel free to use, modify, and distribute.

---

## 🙌 Acknowledgments

- [Ultralytics](https://github.com/ultralytics/ultralytics) — for the amazing YOLO11 implementation
- [OpenCV](https://opencv.org/) — for the powerful computer vision toolkit
- [ByteTrack](https://github.com/ifzhang/ByteTrack) — for the multi-object tracking algorithm

---

## 👤 Author

**Nosayba Manjoud**
- 💼 LinkedIn: [linkedin](www.linkedin.com/in/nosayba-manjoud)
- 🐙 GitHub: [github](https://github.com/NosaybaManjoudAli)
- 📧 Email: nosayba.mahmoud@gmail.com

---
⭐ **If you found this project helpful, please give it a star!** ⭐
