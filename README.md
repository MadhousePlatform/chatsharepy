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

Simply run the Python script:

```bash
python3 chatshare.py
```

Or if you want to make it executable:

```bash
chmod +x chatshare.py
./chatshare.py
```

## Output

The application will output:
```
Welcome to Chatshare!
```

## Testing

Run the unit tests:

```bash
python3 -m unittest test_chatshare.py -v
```

This will run tests for the Chatshare application:
- `test_main_output`: Verifies that the main function prints "Welcome to Chatshare!"

## Linting

Run pylint to check code quality:

```bash
pylint chatshare.py test_chatshare.py
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