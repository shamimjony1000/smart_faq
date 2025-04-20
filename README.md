# Arogga FAQ Assistant

A Flask-based web application that uses the Gemini Flash 2.0 API to provide answers to frequently asked questions about Arogga's services, particularly focusing on Arogga Cash, promotions, and return policies.

## Features

- Interactive chat interface for asking questions
- AI-powered responses using Google's Gemini Flash 2.0 API
- Pre-defined suggestion chips for common questions
- Responsive design that works on desktop and mobile devices

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- A Gemini API key from Google AI Studio

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd FAQ
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.env` file in the project root directory
   - Add your Gemini API key to the `.env` file:
     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

### Running the Application

1. Start the Flask development server:
   ```
   python app.py
   ```

2. Open your web browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## Usage

- Type your question in the input field at the bottom of the chat interface
- Click on the send button or press Enter to submit your question
- Alternatively, click on one of the suggestion chips for quick access to common questions
- The AI assistant will provide an answer based on the FAQ information

## Deployment

For production deployment, consider using Gunicorn as a WSGI server:
```
gunicorn app:app
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
