# https://poker-backend.ddns.net/docs

## installation

Using [uv](https://docs.astral.sh/uv/) as the python project manager for fastapi as the backend server.

```sh
uv sync
```

This creates a venv, downloads deps, also provides python version installation. Essentially like npm for node, or cargo for rust.
It's actually so fast and amazing; adding deps is also easy with just `uv add <pkg-name>`. **USE UV PLEASE**. There's also
`ruff` for formatting; that's more quality of life to keep everything clean. Don't forget to activate your python
virtual environment.

Makefile has most of the required stuff needed to run.

- `dev` (default): dev server
- `run`: prod server
- `format`: ruff to format all python code

## backend details

### GameState schema

This is the internal schema for the json sent to frontend, and the state object managed in the backend.

```py
class Pot:
    value: float  # money in pot
    players: list[str]  # players vying for this pot, team_ids


# cards are defined as 1st char: a(2-9)tjqk, 2nd char: sdch
class GameState:
    index_to_action: int
    players: list[str]  # team_ids
    players_cards: list[list[str]]  # list of two card strs per team by index
    held_money: list[float]  # money per team by index
    bet_money: list[float]  # per round by index, -1 for fold, 0 for check/hasn't bet
    community_cards: list[str]
    pots: list[Pot]  # list for the case of sidepots
    current_round: str  # for convenience: preflop, flop, turn, river
    small_blind: float
    big_blind: float
```

The bot code functions get almost the same schema, EXCEPT `GameState.players_cards` becomes `player_cards` and is just a list of str. In cpp, list becomes vector.

### code execution structure

- NO SAFE GUARDS ON THE CODE!!!
- should be manual checks for no malicious code before running!!!
- submission saves original submitted code file `<team_id>.<py/cpp>` and the `wrapped_<team_id>.<py/cpp>`
- `skeleton_files`: bot code (given to participants) which is inserted into the line of skeleton file that starts with `//%insert%//` (only first occurrence)
- the wrapped file is run with i/o to the bot function with stdin/stdout
- deleting original file doesn't delete the wrapped file, so they technically can still be run (but it don't matter much)
- models for `Pot` and `GameState` for the function are the same for internal, except `players_cards` becomes a single list of the bots' own cards as `player_cards`, not a list of lists
  - vector for cpp

### very broad baseline api

- account for host, human and bot (handled by supabase with frontend or smth)
  - prob should keep track of money for each account
- games, game state: `wss://<ip>:<port>/` like this for obserbing websocket state. prob just get websockets working and everything
- host: control games, start/stop, assigning human players
- human player: send message to websocket with move (only during their turn), can also be used for testing??
- submission: file uploads into template

### additional api stuff

- test games: send in user_ids into a room to battle or smth?

schemas will be figured out as it goes

## general notes

- fastapi + supervisor/systemd + nginx
  - nginx for https/certs, load balancing(?), caching(?), ssl/tls(?), security(?), rate limiting(?)
- sitting on google cloud compute instance
- use external ip for api calls. people don't really see this, so a dns hostname isn't necessary
  - protect routes with auth 😩
- running submitted code files
  - use file with json to provide input. should just give the game state
  - code should fill in a code template that reads json game state and passes that into a function
  - output to stdout
  - python subprocess lib to run
  - install specific executables for specific languages (c++, python, js)
- restricting malicious code
  - c++: no file i/o (fstream, iostream, cstdio), raw mem management or system interaction (memory, cstdlib)
  - py: [restricted python](https://restrictedpython.readthedocs.io/)
  - js: node.js v23.5 has --permission to restrict, deno is already secure by default (tehnically still not safe enough)
- prevent code execution stalling: watch timing, errors of processes
- host to control what players go to what game, tournament manager
- websockets: live updated game state for each game being played in the tournament

## finished tasks (old stuff)

- fastapi setup
- google cloud compute hooked up to static ext ip (35.212.235.70) with a production server than can run on port 8000
- basic websockets for synced gamestate display
  - currently just a chat with all open connections
- file upload to store user submissions
- subprocess to run uploaded code files
  - in the background
  - py, c++ code can be run, return stdout
  - python can access the stdout as a `str` after process finishes

## other ideas

- webhook from github that calls a post request to refresh server with new stuff
  - `subprocess.run("cd /path/to/your/app && git pull origin main && systemctl restart your-service")` on /restart route or smth
  - https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks
- uvicorn multiple workers for more concurrency
