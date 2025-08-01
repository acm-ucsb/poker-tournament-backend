# 35.212.235.70:8000

## wtf bruh.

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

## finished tasks

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
