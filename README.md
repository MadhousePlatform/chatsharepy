# Hello World Python Script

A simple Python script that prints "Hello, World!" to the console.

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
python hello.py
```

Or if you want to make it executable:

```bash
chmod +x hello.py
./hello.py
```

## Output

The script will output:
```
Hello, World!
```

## Testing

Run the unit tests:

```bash
python -m unittest test_hello.py -v
```

This will run two tests:
- `test_main_output`: Verifies that the main function prints "Hello, World!"
- `test_main_returns_none`: Verifies that the main function returns None

## Linting

Run pylint to check code quality:

```bash
pylint hello.py test_hello.py
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