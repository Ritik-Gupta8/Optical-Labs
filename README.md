# Optical Setup Designer

# This is a full-stack web application that allows users to visually configure and simulate optical experiments on a grid.
# The project uses:

- Frontend: Vue 3, Tailwind CSS, Chart.js, and Lucide Icons (all via CDN for single-file simplicity).

- Backend: FastAPI + Python for a high-performance simulation and data service.

# This application provides real-time ray tracing and a frequency sweep analysis. The sweep simulation is context-aware: it checks if a ray path successfully hits a detector and generates a full spectral curve or a flat zero-power line accordingly.

# Local Development Setup
To run the application, you need to execute both the Python backend and serve the HTML frontend.
- Prerequisites

Python 3.8+
A local web server (like VS Code's "Live Server" extension) for serving homepage.html.


1. Setup the Backend (FastAPI)

Ensure all files (app.py, homepage.html, requirements.txt) are in one folder.

Install the required dependencies using the requirements.txt file in your terminal:
    pip install -r requirements.txt

Start the FastAPI server in a terminal (this will auto-reload on code changes):
    uvicorn app:app --reload 

2. Run the Frontend (Vue UI)

The frontend must be served via a local HTTP server to make API calls to the backend.

Using VS Code Live Server:
1. Right-click homepage.html in the VS Code file explorer.
2. Select "Open with Live Server".

The application will open in your browser, ready to communicate with the FastAPI server running o