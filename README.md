# alphaStral

A project by the Rustaceans Teams:

- Adrien Pelfresne [github](https://github.com/dirdr) | [linkedin](https://www.linkedin.com/in/adrien-pelfresne/) | [resume](https://raw.githubusercontent.com/dirdr/resume_adrien_pelfresne/main/raw/resume_adrien_pelfresne_software_engineer.pdf)

  > I'm Adrien Pelfresne, a 22 year old Backend Software engineer specializing in Distributed systems, If you are hiring at this position, please reach out to me :)

- Alexis Vapaille [github](https://github.com/AlexVplle) | [linkedin](https://www.linkedin.com/in/alexis-vapaille/) | [resume](https://alexvplle.com/CV_Alexis_Vapaille.pdf)

>

<img src="logo_team_rustacean.png" alt="drawing" width="200"/>

## About

Fine-tuned vs Foundation, Who will win a Pokemon Showdown Match ?

![David-Goliath](./david_goliath_illustr.webp)

## Run The Battle

### Showdown server

<img src="showdown_logo.png" alt="drawing" width="100"/>

[Pokemon ShowDown](https://en.wikipedia.org/wiki/Pok%C3%A9mon_Showdown) is the biggest Pokemon Battle online plateform. It will be the game engine of the model battle.

Two hosting modes are supported. Choose based on your goal.

---

Local

Battles run fully on your machine. No accounts needed, no rate limits, no internet required.
Since the real showdown instance have some limitation when going brrrr with the training, you might want to pick this option to simulate a lot of battles.

```sh
git clone https://github.com/smogon/pokemon-showdown.git
cd pokemon-showdown
npm install
cp config/config-example.js config/config.js
node pokemon-showdown start --no-security
```

Then run battles:

```sh
uv run python main.py --p1 random --p2 random --n 10
```

---

Public

Battles run on the official Pokémon Showdown server. The only addition of this setup is being able to play against random on the internet.

Requires two registered accounts at [play.pokemonshowdown.com](https://play.pokemonshowdown.com).
Add credentials to `.env` (see `.env.example`), then:

```sh
uv run python main.py --p1 random --p2 random --n 1 --showdown
```

The printed URL lets you spectate the battle live on [play.pokemonshowdown.com](https://play.pokemonshowdown.com).

---

### CLI reference

```
uv run python main.py [OPTIONS]
```

| Argument               | Default            | Description                                                            |
| ---------------------- | ------------------ | ---------------------------------------------------------------------- |
| `--p1`                 | `random`           | Agent for player 1                                                     |
| `--p2`                 | `random`           | Agent for player 2                                                     |
| `--n`                  | `1`                | Number of battles to run                                               |
| `--format`             | `gen9randombattle` | Battle format                                                          |
| `--showdown`           | off                | Use public Showdown server (requires `.env` credentials)               |
| `--move-delay SECONDS` | `0`                | Wait before each move — set to `2`–`3` for comfortable live spectating |
| `--log-level`          | `INFO`             | Verbosity: `DEBUG` `INFO` `WARNING` `ERROR` (also `LOG_LEVEL` env var) |

**Examples**

```sh
# 10 local battles, instant
uv run python main.py --p1 random --p2 random --n 10

# 1 public battle, slowed down for live watching
uv run python main.py --p1 random --p2 random --n 1 --showdown --move-delay 2

# debug everything
uv run python main.py --p1 random --p2 random --n 1 --log-level DEBUG
```

## Model

The battle will be between
