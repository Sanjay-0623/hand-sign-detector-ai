# Hand Sign Detector

Real-time hand sign recognition using AI and computer vision. Train custom hand gestures, detect them in real-time, and convert them to speech.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
  - [Prerequisites](#prerequisites)
  - [Local Setup](#local-setup)
  - [Database Setup](#database-setup)
  - [Vercel Deployment](#vercel-deployment)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Use Cases](#use-cases)
- [Test Cases](#test-cases)
- [Algorithms](#algorithms)
- [Alternative Algorithms](#alternative-algorithms)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Real-time Hand Detection**: Uses MediaPipe Hands to detect and track 21 hand landmarks at 30+ FPS
- **Multiple Detection Modes**:
  - Rule-based gesture recognition (12+ predefined gestures)
  - KNN classifier for custom trained hand signs
  - AI vision detection using GPT-4 Vision API
- **Custom Training**: Train your own hand sign alphabet (A-Z) or custom gestures
- **Cloud Storage**: Training data syncs to Neon PostgreSQL database
- **Sentence Builder**: Combine detected signs to build sentences
- **Text-to-Speech**: Convert detected sentences to speech
- **User Authentication**: Secure login system with bcrypt password hashing
- **Responsive Design**: Works on desktop and mobile devices
- **Dark Theme**: Modern UI with dark mode

## Demo

### Live Demo
Visit: [Your Vercel URL]

### Screenshots

**Training Page**: Train custom hand signs by capturing hand landmarks
**Detection Page**: Real-time gesture detection with visual feedback
**Sentence Builder**: Build and speak sentences from detected signs

## Technology Stack

### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- MediaPipe Hands (Google's hand tracking library)
- Canvas API for video rendering
- Web Speech API for text-to-speech
- LocalStorage for client-side caching

### Backend
- Python 3.9+
- Flask (Web framework)
- psycopg2-binary (PostgreSQL adapter)
- bcrypt (Password hashing)
- python-dotenv (Environment variable management)
- OpenAI GPT-4 Vision API (Optional AI detection)

### Database
- Neon PostgreSQL (Serverless PostgreSQL)
- Two tables: `users` and `training_data`
- JSON storage for hand landmark coordinates

### Deployment
- Vercel (Frontend and Backend hosting)
- Neon (Database hosting)

## Installation

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Neon account (for database) - [Sign up free](https://neon.tech)
- Git (for cloning the repository)
- Modern web browser (Chrome, Firefox, Edge, Safari)

### Local Setup

**Step 1: Clone the Repository**

```bash
git clone https://github.com/yourusername/hand-sign-detector.git
cd hand-sign-detector
```

**Step 2: Install Python Dependencies**

```bash
pip install -r requirements.txt
```

The required packages are:
- Flask
- psycopg2-binary
- bcrypt
- python-dotenv
- requests (for AI API calls)

**Step 3: Configure Environment Variables**

Create a `.env` file in the project root:

```bash
touch .env
```

Add your configuration:

```plaintext
# Database Configuration (Required)
DATABASE_URL=postgresql://username:password@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require

# Session Secret (Required)
SECRET_KEY=your-random-secret-key-here

# AI Detection (Optional - only if using GPT-4 Vision)
AI_API_KEY=your-openai-api-key
AI_PROVIDER=openai
