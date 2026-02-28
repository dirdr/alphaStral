# alphaStral

A project by the Rustaceans Teams:

- Adrien Pelfresne [github](https://github.com/dirdr) | [linkedin](https://www.linkedin.com/in/adrien-pelfresne/) | [resume](https://raw.githubusercontent.com/dirdr/resume_adrien_pelfresne/main/raw/resume_adrien_pelfresne_software_engineer.pdf)
- Alexis Vapaille [github](https://github.com/AlexVplle) | [linkedin](https://www.linkedin.com/in/alexis-vapaille/) | [resume](https://alexvplle.com/CV_Alexis_Vapaille.pdf)

<img src="logo_team_rustacean.png" alt="drawing" width="200"/>

## About

Fine-tuned vs Foundation, Who will win a Pokemon Showdown Match ?

![David-Goliath](./david_goliath_illustr.webp)

## Run The Battle

### Showdown server

Two hosting modes are supported. Choose based on your goal.

---

**Local — for training and benchmarking**

Battles run fully on your machine. No accounts needed, no rate limits, no internet required.
Use this when running many battles to collect stats.

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

**Public — for live spectating**

Battles run on the official Pokémon Showdown server and are watchable live in the browser.
Use this when you want to observe a real confrontation between the two agents.

Requires two registered accounts at [play.pokemonshowdown.com](https://play.pokemonshowdown.com).
Add credentials to `.env` (see `.env.example`), then:

```sh
uv run python main.py --p1 random --p2 random --n 1 --showdown
```

The printed URL lets you spectate the battle live on [play.pokemonshowdown.com](https://play.pokemonshowdown.com).

---

### Start the battle

## Model

The battle will be between
