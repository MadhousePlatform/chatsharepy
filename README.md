# Chatshare

A chat sharing application built with Python.

## Installation

1. Make sure you have Python 3.7+ installed
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

Run the application as a module:

```bash
python3 -m src.chatshare
```

## Output

The application will output:
```
Welcome to Chatshare!
```

## Testing

Run all unit tests:

```bash
python3 -m unittest discover -s tests -p "*.py" -v
```

This will run all tests in the `tests/` directory.

## Linting

Run pylint to check code quality:

```bash
pylint pylint **/*.py
```

This will analyze your code for:
- Style violations
- Potential errors
- Code complexity issues
- Missing docstrings
- And other best practices

## Continuous Integration

This project uses GitHub Actions for continuous integration. The workflow automatically runs on:
- Every push to main/master branch
- Every pull request to main/master branch

The CI pipeline:
- Runs tests on Python 3.12
- Performs linting with pylint
- Caches dependencies for faster builds

You can view the workflow status in the "Actions" tab of this repository. 