# MATCHMYFIT: AI-Powered Apparel Sizing Engine 

> **Eliminating the guesswork from online shopping through Data, AI, and Advanced Computation.**

👉 **[Live Demo / View the live site here]** *https://matchmyfit.streamlit.app/*

MATCHMYFIT is an intelligent size recommendation engine designed to solve the e-commerce challenge of inconsistent clothing sizes. The system analyzes user body measurements, calculates dynamic fabric stretch factors in real-time, and integrates advanced AI tools for data extraction and sentiment analysis to provide highly accurate, personalized size recommendations.

## 🌟 Why This Project Stands Out (Technical Highlights)
This project was built adhering to industry standards, focusing on clean architecture, performance, and maintainability:

* **Object-Oriented Programming (OOP):** The architecture strictly follows OOP principles (Encapsulation, Abstraction, and Separation of Concerns). Core modules like `SizeEngine` and `DatabaseManager` are fully decoupled, making the code modular, secure, and highly testable.
* **Parallelism & Concurrency:** To ensure lightning-fast response times under load, the system utilizes concurrent processing. The core mathematical sizing engine runs in parallel with the AI analyzing buyer reviews and feedback, preventing computational bottlenecks and significantly improving overall performance.
* **AI for Data Processing:** Integrates Large Language Models (LLMs) with complex prompts to convert raw, unstructured data into a structured format the system can reliably process.
* **Comprehensive Unit Testing (TDD):** Includes a full test suite covering edge cases, graceful handling of missing data, and database isolation using temporary test environments (15 dedicated tests).

## ✨ Key Features

* **Closest Match Algorithm:** The engine calculates the distance (Delta) between user measurements and size chart values, selecting the optimal size by factoring in fit preferences and fabric stretch, even when a 100% exact match isn't available.
* **AI-Driven Size Chart Extraction:** Intelligently analyzes a user-uploaded size chart, extracts the raw data, and automatically converts it into a clean, actionable JSON format.
* **AI Sentiment Analysis:** Utilizes AI models to analyze the text of buyer reviews and feedback, extracting meaningful insights about garment fit and sizing trends.
* **Smart Fabric Stretch Calculation:** Dynamically calculates a "Weighted Stretch" score based on precise fabric composition (e.g., 90% Cotton, 10% Elastane).
* **Personal Digital Closet:** A dedicated space where users can view their garment history, displaying a clear breakdown of recommended sizes based on past data and core fabric types.
* **Dynamic Size Normalization:** Seamlessly converts diverse sizing formats (Alpha e.g., S/M/L, Numeric, and One-Size) into a standardized, unified data model.

* **Anatomical Data Normalization:** The engine includes a smart auto-correction algorithm that detects irregular size chart formats (e.g., flat "armpit" measurements common in fast fashion like Zara) and normalizes them into standard "Full Bust" equivalents for flawless matching.

* **Interactive UI & Measurement Guide:** Features a built-in, user-friendly measurement guide to ensure the data inputted by the user is structurally accurate, preventing "garbage-in, garbage-out" scenarios.

* **Fit Preference Customization:** Adjusts mathematical calculation tolerances ("Ease") based on the user's preferred clothing style: *Slim, Regular, or Oversized*.

## 🏗️ Architecture & Tech Stack
* **Language:** Python 3.x
* **Frontend / UI:** Streamlit
* **Database:** SQLite (Relational Data Modeling with Unique Key constraints)
* **Architecture:** Modular OOP, Concurrent Processing
* **Quality Assurance:** `unittest` framework

## 🚀 Getting Started 

💡 Quick Start Tip: You can log in using the pre-configured test account: test@matchmyfit.com to immediately test the sizing engine without registering.

You can run this project locally using Python, or spin it up instantly using Docker.

### Option 1: Run with Docker 🐳 (Recommended)
Run the following commands in your terminal to clone the repository, build the image, and run the test suite in an isolated container:


```bash
git clone https://github.com/galbigi/MATCHMYFIT.git
cd MATCHMYFIT
docker build -t matchmyfit-engine .
docker run -p 8501:8501 --env-file .env matchmyfit-engine
```
### Option 2: Local Development Setup 💻 (Windows)
If you prefer to run the code locally without Docker, run the following sequence in your terminal:

```bash
git clone https://github.com/galbigi/MATCHMYFIT.git
cd MATCHMYFIT
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
python test_logic.py
```