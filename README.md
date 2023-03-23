# Jerbot version 4 ("Reheated")

## About
Jerbot is a generic, extensible, modular multi-purpose Discord bot. It primarily caters to the needs of the [Binding of Isaac Discord server](https://discord.gg/isaac), but is used sparingly in Nuclear Throne, Linux Gaming and a few other servers. 

Jerbot's flexible configuration system allows for hot-toggling of features (or subfeatures, barring some edge cases!) for every server it's deployed on. There are *no* global commands- everything is done on a server by server basis.


## Running
### [FOLLOW FIRST] Initial setup
`git clone` the repository, then
- Copy `config.sample.yaml` to `config.yaml`.
- Tweak the `config.yaml` to your liking. Make sure your bot's token is correct, and that, if you plan to use any submodules like [Book of Secrets](https://github.com/boi-community/book-of-secrets), make sure the folder is added to `plugin_folders`.
- In `server_configs`, copy `server_config.sample.yaml` to `(guild id).yaml`, where `(guild id)` is the ID of a guild you are going to deploy the bot in. Every guild the bot is in will need its own config.
- Tweak every planned server config to your liking.


### Docker Compose (Highly Recommended)
If you haven't used Docker or Docker Compose before, [you'll need to install it.](https://docs.docker.com/engine/install/) I highly recommend checking it out- it makes running this stuff much easier!

- Optionally, uncomment the commented out plugins line in `docker-compose.yml`. This means that if the only changes in a commit are to plugins instead of the main bot, the plugins can simply be reloaded in place instead of requiring a container restart.
- Initialize the bot with `docker compose up`.


### Docker
- Build the bot with `docker build --tag jerbot`.
- Then, run the bot. There's a few bind mounts you'll need to make.
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

- (Optional, highly recommended) Create a virtualenv:
```bash
python3 -m virtualenv venv
source venv/bin/activate
```
- Run the bot: `python3 main.py`
