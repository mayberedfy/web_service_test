# Flask Web Service

This project is a simple web service built using Flask. It serves as a template for creating web applications with Python and is managed using the `uv` package manager.

## Project Structure

```
flask-web-service
├── src
│   ├── app.py            # Entry point of the application
│   ├── routes            # Contains route definitions
│   │   └── __init__.py
│   └── models            # Contains data models
│       └── __init__.py
├── tests                 # Contains unit tests
│   └── test_app.py
├── pyproject.toml       # Project configuration and dependencies
├── uv.lock              # Dependency lock file
└── README.md            # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd flask-web-service
   ```

2. **Install dependencies:**
   Use the `uv` package manager to install the required dependencies:
   ```
   uv install
   ```

3. **Run the application:**
   Start the Flask application:
   ```
   python src/app.py
   ```

4. **Run tests:**
   To ensure everything is working correctly, run the tests:
   ```
   python -m unittest discover -s tests
   ```

## Usage

Once the application is running, you can access it at `http://127.0.0.1:5000`. You can extend the functionality by adding new routes and models as needed.

## Contributing

Feel free to submit issues or pull requests if you have suggestions or improvements for the project.