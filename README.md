# Jerbot version 4 ("Reheated")

## About
Jerbot is a generic, extensible, modular multi-purpose Discord bot. It primarily caters to the needs of the [Binding of Isaac Discord server](https://discord.gg/isaac), but is used sparingly in Nuclear Throne, Linux Gaming and a few other servers. 

Jerbot's flexible configuration system allows for hot-toggling of features (or subfeatures, barring some edge cases!) for every server it's deployed on. There are *no* global commands- everything is done on a server by server basis.

## Configuration
Sample global and server-specific configuration files are located in the repo. Please see [config.sample.yaml](config.sample.yaml) and [server_config.sample.yaml](server_configs/server_config.sample.yaml) for more info.

## Running
### Docker (Highly Recommended)
I haven't submitted the bot to GHCR or Docker Hub yet, but plan to as soon as the bot is running in production. For now, use the Dockerfile. If you haven't used Docker before, [you'll need to install it.](https://docs.docker.com/engine/install/) I highly recommend checking it out- it makes running this stuff much easier!


`git clone` the repository, then build the image:

```bash
docker build --tag jerbot
```

Then, run the bot. There's a few bind mounts you'll need to make (when the bot is submitted to GHCR or Docker Hub, I'll supply a `docker-compose.yml `to make this easier.)
```bash
docker run \
    -v "/full/path/to/your/config.yaml":/jerbot/config/yaml \
    -v "/full/path/to/your/server_configs":/jerbot/server_configs \
    -v "/full/path/to/your/db_folder":/jerbot/db \
    jerbot
```

### Manually (Not recommended, unsupported)
**A minimum of Python 3.10 is required.** I have not tested the bot on any later versions.

These instructions are for Linux, but should work for macOS as well. I have not tested Windows, but the only difference should be the activating the virtualenv.

`git clone` the repository, then:

(Optional, highly recommended) Create a virtualenv:
```bash
python3 -m virtualenv venv
source venv/bin/activate
```
Run the bot:
```bash
python3 main.py
```