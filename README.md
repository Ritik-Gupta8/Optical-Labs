# Optical Setup Designer

# This is a full-stack web application that allows users to visually configure and simulate basic optical experiments on a grid.
The project uses:
    Frontend: Vue 3 (via CDN for single-file simplicity) + Tailwind CSS for a modern User Interface.
    Backend: FastAPI + Python for a high-performance simulation and data service.

# Local Development Setup
    To run the application, you need to execute both the Python backend and serve the HTML frontend.
# Prerequisites
    Python 3.8+
    VS Code Live Server Extension for serving index.html.

# Setup the Backend (FastAPI)
    Ensure all files are in one folder.
    Install the required dependencies using the requirements.txt file in terminal:
        pip install -r requirements.txt

# Start the FastAPI server in a terminal:
    uvicorn app:app --reload

# Run the Frontend (Vue UI)
    The frontend must be served via a local HTTP server to make API calls.
    VS Code Live Server : Right-click index.html in VS Code and select "Open with Live Server".
    The application will open in your browser, ready to communicate with the FastAPI server running on port 8000.