# nft-twitter-bot

This project is a simple bot that tweets every time an NFT is listed on a marketplace. It monitors the NFT listings and sends out tweets using the Twitter API.

## Project Structure

```
nft-twitter-bot
├── src
│   ├── bot.py                # Main entry point for the bot
│   ├── config.py             # Configuration settings for the bot
│   ├── nft_monitor.py         # Monitors the NFT marketplace for new listings
│   ├── twitter_client.py      # Handles interactions with the Twitter API
│   └── utils
│       └── helpers.py        # Utility functions used throughout the project
├── tests
│   ├── __init__.py           # Marks the tests directory as a package
│   ├── test_bot.py           # Unit tests for bot.py functionality
│   └── test_nft_monitor.py    # Unit tests for nft_monitor.py functionality
├── .env.example               # Example of environment variables needed for the project
├── requirements.txt           # Python dependencies required for the project
└── README.md                  # Documentation for the project
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd nft-twitter-bot
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Set up your environment variables by copying `.env.example` to `.env` and filling in the necessary API keys.

## Usage

To run the bot, execute the following command:
```
python src/bot.py
```

Make sure to monitor the console for any logs or errors.

## Contributing

Feel free to submit issues or pull requests for any improvements or bug fixes.