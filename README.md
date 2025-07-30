# 35.212.235.70:8000

## wtf bruh.

- fastapi + supervisor/systemd + nginx
  - nginx for https/certs, load balancing(?), caching(?), ssl/tls(?), security(?), rate limiting(?)
- sitting on google cloud compute instance
- use external ip for api calls. people don't really see this, so the ip doesn't really matter.
  - protect routes with auth 😩
- use files to determine output of functions called from the code written
  - output to text
- install specific executables for specific languages (c++, python, js) with drop-in templates for poker function

## other ideas

- webhook from github that calls a post request to refresh server with new stuff
  - `subprocess.run("cd /path/to/your/app && git pull origin main && systemctl restart your-service")` on /restart route or smth
  - https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks
- uvicorn multiple workers for more concurrency
