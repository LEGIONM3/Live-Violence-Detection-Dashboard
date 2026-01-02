# Live Violence Monitoring System

A real-time AI-powered violence detection and monitoring system designed to enhance security surveillance. This application utilizes deep learning models (Conv3D, SlowFast) to analyze video feeds and detect violent activities, providing instant alerts and a comprehensive dashboard for monitoring. Supports secure user management, incident logging, and multi-channel notifications.

## 🚀 Features

*   **Real-time Violence Detection**: Analyzes live video streams to detect violent events with high accuracy using deep learning models.
*   **Live Monitoring Dashboard**: A user-friendly React-based frontend to view live camera feeds and detection status.
*   **Deep Learning Models**: Supports advanced architectures like Conv3D and SlowFast for robust video action recognition.
*   **Alert System**: Configurable alerts via Email (Gmail) and Telegram to notify administrators immediately upon detection.
*   **User Management**: Secure authentication and role-based access control (Admin/User).
*   **incident History**: Logs detection events and live sessions for audit and review.
*   **API-First Design**: Built with FastAPI for high performance and easy integration.

## 🧠 AI & Machine Learning Models

This project implements multiple state-of-the-art architectures for Video Action Recognition to ensure robust detection of violent activities:

1.  **ViolenceConv3D (C3D)**
    *   A 3D Convolutional Neural Network (CNN) that processes video frames as a 3D volume (Time x Height x Width).
    *   Effectively captures spatial and temporal features simultaneously.
    *   *Best for:* General violence detection with balanced performance.

2.  **SlowFast Network**
    *   Implements the SlowFast architecture (by Facebook AI Research), which uses two parallel pathways:
        *   **Slow Pathway**: Low frame rate, captures spatial semantics.
        *   **Fast Pathway**: High frame rate, captures motion at fine temporal resolution.
    *   *Best for:* Detecting rapid motions and fighting scenes.

3.  **ViolenceGRU (CNN + RNN)**
    *   Combines a 2D CNN (feature extractor) with a Gated Recurrent Unit (GRU).
    *   The CNN extracts features from each frame, and the GRU analyzes the sequence of features over time.
    *   *Best for:* Longer temporal dependencies and analyzing sequence progression.

4.  **Two-Stream Network**
    *   Processes RGB frames (for appearance) and Optical Flow (for motion) separately.
    *   Fuses the results from both streams for a final prediction.
    *   *Best for:* High-accuracy scenarios where motion patterns are critical.

## 🛠️ Tech Stack

### Backend
*   **Language**: Python 3.13+
*   **Framework**: FastAPI
*   **Database**: SQLite (Async via SQLAlchemy & aiosqlite)
*   **ML Libraries**: PyTorch, Torchvision, PyTorchVideo, OpenCV
*   **Authentication**: JWT (JSON Web Tokens)

### Frontend
*   **Framework**: React (Vite)
*   **Styling**: Tailwind CSS, Vanilla CSS
*   **State Management**: React Hooks

## 📋 Prerequisites

*   **Python**: Version 3.10 or higher (Tested with 3.13)
*   **Node.js**: Version 18 or higher
*   **NPM**: Installed with Node.js

## ⚡ Installation & Setup

### 1. Backend Setup

Navigate to the backend directory and set up the Python environment.

```bash
cd backend
# Create a virtual environment (if not already created)
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
```

**Run the Backend:**

```bash
# Make sure you are in the backend directory with venv activated
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```
The API will be available at `http://127.0.0.1:8001`.
*   **Docs**: `http://127.0.0.1:8001/docs`
*   **Health Check**: `http://127.0.0.1:8001/health`

### 2. Frontend Setup

Open a new terminal, navigate to the frontend directory, and install dependencies.

```bash
cd frontend
npm install
```

**Run the Frontend:**

```bash
npm run dev
```
The application will launch at `http://localhost:5173`.

## 👤 Default Credentials

Upon first startup, the system creates a default administrator account:

*   **Email**: `admin@example.com`
*   **Password**: `admin123`

> ⚠️ **Important**: Please change this password immediately after logging in for the first time.

## 📂 Project Structure

```
live-violence-monitoring/
├── backend/                # FastAPI application
│   ├── app/                # Application source code (API, Core, Models, Services)
│   ├── models/             # ML Model weights directory
│   ├── requirements.txt    # Python dependencies
│   └── venv/               # Python Virtual Environment
├── frontend/               # React application
│   ├── src/                # Frontend source code
│   └── package.json        # Node.js dependencies
└── README.md               # Project Documentation
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📄 License

This project is licensed under the MIT License.
