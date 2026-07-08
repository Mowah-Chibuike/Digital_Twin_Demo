````markdown
# 🚀 Live MQTT IMU Visualizer & Background Video Exporter

A high-performance **PyQt5** desktop application that subscribes to real-time IMU telemetry over **MQTT**, visualizes orientation in an interactive **OpenGL 3D environment**, logs telemetry sessions to **SQLite**, and exports recorded sessions as **MP4 videos** using **OpenCV**—all while keeping the user interface responsive through background worker threads.

---

## ✨ Features

- **Real-Time MQTT Streaming**
  - Asynchronously subscribes to IMU telemetry using a dedicated `QThread`.
  - Processes incoming JSON messages without blocking the GUI.

- **Hardware-Accelerated 3D Visualization**
  - Custom `QOpenGLWidget` renders live roll, pitch, and yaw orientation.
  - Smooth, real-time visualization powered by OpenGL.

- **Live Orientation Calibration (Tare)**
  - Instantly resets the current sensor orientation as the new zero reference.
  - Useful when the sensor is mounted at an angle or repositioned.

- **SQLite Data Logging**
  - Records timestamped telemetry sessions locally.
  - Automatically organizes recordings by unique session IDs.

- **Background MP4 Video Export**
  - Exports recorded sessions into MP4 videos using OpenCV.
  - Rendering is performed in a dedicated worker thread.
  - Offscreen OpenGL rendering ensures the main visualization remains uninterrupted.

---

# 🏗️ System Architecture

```text
[ Physical IMU Sensor ]
         │ (WiFi / Cellular JSON)
         ▼
[ MQTT Broker ]
         │
         ▼
┌────────────────────────────────────────────────────────┐
│                 PyQt5 Desktop Application              │
│                                                        │
│  ┌───────────────────────┐      ┌───────────────────┐  │
│  │ MQTTTelemetryWorker   │ ───► │ MainWindow GUI    │  │
│  │ (Background Thread)   │      │ (Main Thread)     │  │
│  └───────────────────────┘      └─────────┬─────────┘  │
│                                           │            │
│                  ┌────────────────────────┴────┐       │
│                  ▼                             ▼       │
│      ┌─────────────────────┐      ┌─────────────────┐ │
│      │ IMUVisualizerWidget │      │ SQLite Database │ │
│      │  OpenGL Rendering   │      │   imu_data.db   │ │
│      └─────────────────────┘      └────────┬────────┘ │
│                                            │          │
│                       Export Session       │          │
│                              ▼             │          │
│                  ┌─────────────────────┐   │          │
│                  │ Hidden OpenGL Widget│   │          │
│                  │ Offscreen Renderer  │   │          │
│                  └──────────┬──────────┘   │          │
│                             ▼              │          │
│                   ┌────────────────────┐   │          │
│                   │ VideoExportWorker  │───┘          │
│                   │  OpenCV Thread     │              │
│                   └─────────┬──────────┘              │
└─────────────────────────────┼─────────────────────────┘
                              ▼
                     Generated MP4 Video
```

---

# 📦 Technology Stack

- **Python**
- **PyQt5**
- **PyOpenGL**
- **Paho MQTT**
- **SQLite**
- **OpenCV**
- **NumPy**

---

# 📥 Installation

Clone the repository and install the required Python packages.

```bash
pip install pyqt5 pyopengl paho-mqtt opencv-python numpy
```

### Linux Users

If you're running a minimal Linux distribution, install the OpenGL runtime:

```bash
sudo apt install libgl1-mesa-glx
```

---

# 🚀 Getting Started

Launch the application:

```bash
python main.py
```

---

# 📡 MQTT Configuration

The application subscribes to an MQTT topic carrying IMU orientation data.

**Broker**

```text
broker.hivemq.com
```

**Topic**

```text
my_angles
```

### Expected Payload

```json
{
    "x": 12.45,
    "y": -45.21,
    "z": 90.00
}
```

Where:

- **x** → Roll (°)
- **y** → Pitch (°)
- **z** → Yaw (°)

---

# 🧭 Using the Application

## Reset Orientation

If the sensor is not perfectly level, place it in the desired reference position and click:

```
Reset Orientation
```

The current orientation becomes the new zero reference for all axes.

---

## Record a Session

1. Click **Record**.
2. Telemetry is stored under a unique session ID.

Example:

```text
RUN_20250710_153255
```

3. Use **Pause** to temporarily stop recording.
4. Click **Stop** to finalize the recording.

---

## Export a Recording

Navigate to:

```
Playback
    └── View All Recordings
```

Then:

1. Select a recording.
2. Click:

```
Export Selected Session to Video (Background)
```

The recording is rendered into an MP4 file while the application remains fully responsive.

---

# 📂 Project Structure

```text
.
├── main.py
├── imu_data.db
├── video_RUN_xxx.mp4
└── README.md
```

---

# ⚡ Performance Highlights

- Dedicated MQTT listener thread
- Responsive PyQt5 GUI
- Hardware-accelerated OpenGL rendering
- SQLite-backed telemetry storage
- Non-blocking video export
- Offscreen GPU rendering pipeline
- Background OpenCV encoding
- Suitable for long-duration telemetry visualization

---

# 📄 License

This project is licensed under the **MIT License**.

You are free to use, modify, and distribute this software for personal, academic, and commercial robotics applications.
````
