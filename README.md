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

### Environment Configuration

Before running the application, you need to set up the following environment variables in a `.env` file:

- `PANEL_API_URL`: URL for the panel API (e.g. https://peli.sketchni.uk/api/)
- `PANEL_APPLICATION_KEY`: Your panel application key for authentication <sup>\*</sup>
- `PANEL_CLIENT_KEY`: Your panel client key for authentication <sup>\*\*</sup>
- `DISCORD_TOKEN`: Your Discord bot token
- `DISCORD_CHANNEL`: The Discord channel ID to interact with

<sup>
<p>* - This is generated in the admin panel of Pterodactyl/Pelican.</p>
<p>** - This is generated in the user settings of Pterodactyl/Pelican</p>
</sup>

You can create a `.env` file in the project root with these variables:

```
PANEL_API_URL=https://example.com/api/
PANEL_APPLICATION_KEY=your_application_key
PANEL_CLIENT_KEY=your_client_key
DISCORD_TOKEN=your_discord_token
DISCORD_CHANNEL=your_channel_id
```

An example file `.env.example` is provided for reference.

### Starting the Application

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
pylint **/*.py
```

This will analyse your code for:

- Style violations
- Potential errors
- Code complexity issues
- Missing docstrings
- And other best practices

## Continuous Integration

This project uses GitHub Actions for continuous integration. The workflow automatically runs on:

- Every push to the main branch
- Every pull request to the main branch

The CI pipeline:

- Runs tests on Python 3.12
- Performs linting with pylint
- Caches dependencies for faster builds

You can view the workflow status in the "Actions" tab of this repository.
