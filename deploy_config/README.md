# config

## vm instance things

- firewall rules to allow http, https

## vm instance set up

- install `git`, set up ssh keys for private repo access
- clone repo into home directory
- install `uv`, `make`
- add `.env` file with supabase environment variables
- install `nginx`
- place nginx_block.conf into `/etc/nginx/sites-enabled/`
- install and run `certbot` for nginx to get https and secured connections
- create systemd service unit file for project
  - these are here: `/etc/systemd/system/<service-name>.service`
  - after editing, refresh daemon for new unit file changes with `sudo systemctl daemon-reload`
  - start service `sudo systemctl start <service-name>`
- make sure nginx and fastapi services are enabled, so they run automatically

```sh
sudo systemctl enable nginx
sudo systemctl enable fastapi
```

- start systemd and services. if already running, use restart instead of start

```sh
sudo systemctl start nginx
sudo systemctl start fastapi
```

- can also check status with `sudo systemctl status <service-name>`
- update fastapi production deployement after pulling from git with `sudo systemctl restart fastapi`
