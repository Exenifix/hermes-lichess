# hermes-lichess
Just an https://lichess.org bot API client for playing games. **This is not a chess engine**

# Setup

1. Install requirements
```sh
$ pip install -r requirements.txt
```

2. Create a new `.env` file with the following contents, correspondingly replacing `your_lichess_token` with your lichess token and `/path/to/your/engine` with the path to your chess engine executable:
```env
TOKEN=your_lichess_token
PATH_TO_ENGINE=/path/to/your/engine
```

# Running

Run the `main.py`.
