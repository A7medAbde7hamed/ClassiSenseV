# ClassiSense

## AI-Powered Smart Classroom Monitoring & IoT System

ClassiSense is an intelligent classroom monitoring system that combines **Computer Vision, Artificial Intelligence, Data Science, and IoT** to monitor classroom occupancy, environmental conditions, and safety in real time.

The system uses a camera to analyze the classroom and estimate the number of students present. An Arduino or ESP32 connects directly to the Computer Vision computer (for example, through USB Serial) to provide sensor readings and receive device-control commands. The API layer is reserved for communication between the Computer Vision application and the frontend dashboard; the microcontroller does not need to communicate with the backend API.

The collected data is stored and analyzed to discover patterns, visualize classroom behavior, and build Machine Learning models that can make predictions and intelligent decisions.

Based on the detected conditions, the Computer Vision application can send control commands directly to the Arduino or ESP32, which operates classroom devices such as lights and alarms. Local safety actions should not depend on the dashboard or network being available.

---

## Project Objectives

The main objectives of ClassiSense are:

* Detect and count students inside a classroom using Computer Vision.
* Monitor classroom environmental conditions using IoT sensors.
* Automatically control classroom lighting based on occupancy.
* Detect dangerous situations and trigger safety alerts.
* Collect and store real-time classroom data.
* Analyze collected data using Data Science techniques.
* Visualize classroom statistics and patterns.
* Apply Machine Learning for prediction and anomaly detection.
* Demonstrate the integration between AI, Data Science, and IoT in a real-world scenario.

---

# System Overview

The system has three main parts: the Computer Vision application, the directly connected IoT controller, and the dashboard/backend software.

```text
                    Physical Classroom
                           |
              +------------+------------+
              |                         |
            Camera                 Sensors / Devices
              |                         |
              v                         v
      Computer Vision  <---Serial---> Arduino / ESP32
      (Python, OpenCV,                  |   |
       YOLO, decision logic)            |   +--> Lights / Buzzer / Relays
              |
              | REST API (software data only)
              v
        Backend / API Layer
              |
        +-----+------+
        |            |
        v            v
    Database    Frontend Dashboard
        |
        v
 Historical Data / Data Science / ML
```

**Communication rule:** the Arduino/ESP32 connects directly to the Computer Vision application, typically over USB Serial for the first implementation. The API is used only for exchanging application data between the Computer Vision side and the dashboard software through the backend. There is no separate API connection between the microcontroller and the backend.
---

# Main Features

## 1. Student Detection & Counting

A camera monitors the classroom and Computer Vision is used to detect people.

The system can determine:

* Number of students currently inside the classroom.
* Classroom occupancy percentage.
* Occupancy changes over time.
* Entry and exit activity.

Example:

```text
Students Detected: 24
Occupancy: 80%
Status: Occupied
```

---

## 2. Smart Lighting

The system uses classroom occupancy information to control the lights.

For example:

```text
Students = 0
        |
        v
Classroom Empty
        |
        v
Lights OFF
```

When students are detected:

```text
Students > 0
        |
        v
Classroom Occupied
        |
        v
Lights ON
```

A delay can be added to prevent the lights from turning off because of temporary detection errors.

---

## 3. Environmental Monitoring

The ESP32 collects environmental data using different sensors.

Possible measurements include:

* Temperature
* Humidity
* Light intensity
* Air quality / CO2
* Other environmental measurements depending on available hardware

Example:

```text
Temperature: 26°C
Humidity: 48%
Light: 350 lux
CO2: 850 ppm
```

---

## 4. Safety Monitoring

The system can monitor potentially dangerous conditions.

For example:

* Fire / flame detection
* Smoke detection
* Abnormal temperature
* Other safety-related sensor readings

When a dangerous condition is detected:

```text
Danger Detected
      |
      v
ESP32
      |
 +----+----+
 |         |
 v         v
Buzzer   Warning
```

The Computer Vision application can forward an alert to the dashboard through the API. The Arduino/ESP32 should still activate its local buzzer or other local safety output directly when the connected safety sensor detects a configured danger condition.

---

# Artificial Intelligence & Computer Vision

ClassiSense uses Computer Vision to understand the classroom environment from camera input.

### Technologies

* Python
* OpenCV
* YOLO or another suitable object detection model

OpenCV is responsible for image and video processing, while the detection model is used to identify objects such as people.

Example pipeline:

```text
Camera
   |
   v
Video Frame
   |
   v
OpenCV
   |
   v
Object Detection Model
   |
   v
Person Detection
   |
   v
People Count
```

The project may also use Computer Vision / AI models for safety detection such as fire or smoke detection, depending on the final implementation.

---

# Data Science

Data Science is an important part of ClassiSense.

The Computer Vision application receives sensor readings directly from the connected Arduino/ESP32 and combines them with occupancy results before sending relevant data to the backend for storage.

Example dataset:

| Timestamp | Students | Temperature | Humidity | Light | Fire |
| --------- | -------: | ----------: | -------: | ----: | ---- |
| 09:00     |       12 |        24.1 |       45 |   320 | 0    |
| 10:00     |       25 |        25.2 |       48 |   350 | 0    |
| 11:00     |       31 |        27.0 |       52 |   280 | 0    |
| 12:00     |        0 |        25.8 |       49 |   300 | 0    |

This data can be used for:

* Exploratory Data Analysis (EDA)
* Data cleaning
* Data visualization
* Correlation analysis
* Occupancy analysis
* Energy usage analysis
* Anomaly detection
* Machine Learning

---

# Machine Learning

Machine Learning can be used to make predictions based on historical classroom data.

Possible ML tasks include:

### Classroom Occupancy Prediction

Predict the expected number of students based on:

* Time
* Day
* Previous occupancy
* Temperature
* Classroom schedule
* Historical data

Example:

```text
Input:
Day       = Monday
Time      = 10:00 AM
Previous  = 22 Students

Prediction:
Expected Occupancy = 27 Students
```

### Anomaly Detection

The system can identify unusual classroom conditions.

For example:

```text
Normal Occupancy: 15 - 30 students

Detected:
58 students

Result:
Occupancy Anomaly
```

The exact Machine Learning model will depend on the collected dataset and the final project requirements.

---

# IoT System

The hardware controller can be an **Arduino Uno** or an **ESP32**. It connects directly to the computer running the Computer Vision application, rather than sending sensor data to the backend itself.

The direct connection can use:

* **USB Serial** — recommended for the initial prototype and suitable for either Arduino Uno or ESP32.
* **Wi-Fi** — optional for a later ESP32-based implementation if wireless communication is needed. The project does not require the ESP32 to call backend APIs.

The microcontroller is responsible for:

* Reading connected sensor values.
* Sending sensor readings to the Computer Vision application over the direct connection.
* Receiving control commands from the Computer Vision application.
* Controlling lights, relays, LEDs, and buzzers.
* Performing essential local safety actions without depending on the dashboard or internet connection.

Possible hardware components:

### Main Controller

* Arduino Uno R3 or ESP32 Development Board

### Sensors

Depending on the final implementation:

* DHT22 / DHT11 — Temperature & Humidity
* LDR — Light Intensity
* MQ-series sensor or suitable air-quality sensor
* Flame Sensor
* Smoke Sensor
* Additional sensors if required

### Actuators

* LED / LED Strip or small DC light
* Buzzer
* Relay Module
* Optional OLED/LCD Display

**Safety note:** prototype flame/smoke sensors are not certified fire-alarm equipment. Any real-world installation must retain suitable certified fire-safety systems.
---

# Software Architecture

The Computer Vision application is the integration point for the camera and the directly connected IoT controller. The dashboard does not communicate with the microcontroller directly.

```text
Camera --> Computer Vision / AI Application <--> Arduino or ESP32
                         |
                         | REST API
                         v
                   Backend Services
                         |
                    PostgreSQL
                         |
                         v
                Frontend Dashboard
```

The Computer Vision application:

* Processes camera frames and calculates classroom occupancy.
* Receives sensor readings from the Arduino/ESP32 over the direct connection.
* Applies decision logic and sends device-control commands back to the controller.
* Sends occupancy, sensor data, and alerts to the backend through the API for display and storage.

The backend provides the API used by the Computer Vision application and dashboard software, validates and stores incoming data, and serves the information needed by the dashboard. The Arduino/ESP32 does **not** call these APIs.

The initial direct hardware connection can use USB Serial. ESP32 Wi-Fi or MQTT may be considered as a future option, but is not required for the architecture described here.
---

# Suggested Technology Stack

## Hardware

* ESP32
* DHT11 / DHT22
* LDR
* Flame Sensor
* Smoke / Air Quality Sensor
* Buzzer
* LEDs
* Relay Module
* Optional OLED/LCD
* Camera / Webcam

## Computer Vision & AI

* Python
* OpenCV
* YOLO
* NumPy
* Optional: PyTorch

## Data Science

* Python
* Pandas
* NumPy
* Matplotlib
* Seaborn
* Scikit-learn
* Jupyter Notebook

## Backend

* Java
* Spring Boot
* REST APIs
* PostgreSQL

## Communication

* USB Serial between the Computer Vision computer and Arduino/ESP32 (initial implementation)
* HTTP/REST API between the Computer Vision application and the backend/dashboard software
* Optional ESP32 Wi-Fi or MQTT in a future version; not required for the initial design

## Development Tools

* IntelliJ IDEA
* VS Code
* Arduino IDE
* Jupyter Notebook
* Git & GitHub
* Postman

---

# Data Flow

The complete system follows this process:

```text
1. Camera captures classroom video
                |
                v
2. Computer Vision detects and counts people
                |
                +<---- Direct Serial connection ----> Arduino / ESP32
                |                                      |          |
                |                               Sensor readings  Device control
                |                                      |          |
                +<--------------------------------------+          v
                |                                         Lights / Buzzer
                v
3. Computer Vision sends occupancy, sensor readings, and alerts
   to the backend through the REST API
                |
                v
4. Backend validates and stores data in PostgreSQL
                |
                v
5. Dashboard retrieves and displays current and historical data
                |
                v
6. Data Science / ML analyzes historical data when sufficient data exists
```

The microcontroller communicates directly with the Computer Vision application. API communication is limited to the software data path between the Computer Vision application and the dashboard/backend. Local device control does not depend on an API request.
---

# Example Scenario

### Classroom is Empty

```text
Camera:
Students = 0

Arduino / ESP32 (directly connected):
Temperature = 25°C
Humidity = 45%

Computer Vision application:
Classroom = Empty

Direct command to Arduino / ESP32:
Lights = OFF
```

### Students Enter

```text
Camera:
Students = 18

Computer Vision application:
Classroom = Occupied

Direct command to Arduino / ESP32:
Lights = ON
```

### Dangerous Condition

```text
Fire Detection:
Detected

Arduino / ESP32:
Activate local buzzer when configured safety sensor triggers

Computer Vision application:
Safety Status = DANGER

API to dashboard software:
Alert = Sent
```

---

# Data Visualization

The dashboard can display real-time and historical information such as:

* Current number of students
* Classroom occupancy
* Temperature
* Humidity
* Light level
* Safety status
* Occupancy over time
* Environmental changes
* Predicted occupancy
* Detected anomalies

Example:

```text
Students Over Time

40 |             *
30 |        *    * *
20 |   *    * *  * *
10 | * *    * *
 0 +--------------------
    9   10   11   12
```

---

# Project Structure

A possible project structure:

```text
ClassiSense/
│
├── computer-vision/
│   ├── detection/
│   ├── hardware-serial/
│   ├── models/
│   └── main.py
│
├── data-science/
│   ├── datasets/
│   ├── notebooks/
│   ├── preprocessing/
│   └── models/
│
├── iot/
│   ├── arduino/
│   └── esp32/
│
├── backend/
│   └── spring-boot/
│
├── dashboard/
│
├── database/
│
├── docs/
│
└── README.md
```

The exact folder names may change as implementation progresses. The key design decision is that `computer-vision/` communicates directly with the microcontroller, while the API is used for data exchange with the backend/dashboard software.
---

# Expected Results

The final system should be able to:

* Monitor classroom occupancy in real time.
* Count students using Computer Vision.
* Collect environmental IoT data.
* Automatically control classroom lighting.
* Detect dangerous conditions.
* Trigger safety alerts.
* Store historical data.
* Analyze classroom behavior using Data Science.
* Visualize collected data.
* Apply Machine Learning for prediction or anomaly detection.
* Demonstrate direct communication between the Computer Vision application and IoT hardware, plus API-based data exchange with the dashboard software.

---

# Future Improvements

Possible future improvements include:

* Face recognition for automated attendance.
* More advanced occupancy prediction.
* Energy consumption prediction.
* Advanced fire and smoke detection.
* Mobile application.
* Cloud deployment.
* Multiple classroom support.
* Centralized monitoring for an entire building.
* Real-time notifications.
* More advanced Machine Learning models.

---

# Team

ClassiSense is developed as an academic project combining:

* Internet of Things (IoT)
* Computer Vision
* Artificial Intelligence
* Data Science
* Machine Learning
* Backend Development

The project is designed to demonstrate how these technologies can work together to create an intelligent and automated classroom environment.
