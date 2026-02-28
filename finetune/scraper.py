import requests
import json
import time
from pathlib import Path

REPLAY_SEARCH_URL = "https://replay.pokemonshowdown.com/search.json"
REPLAY_URL = "https://replay.pokemonshowdown.com/{id}.json"
POKEAPI_POKEMON = "https://pokeapi.co/api/v2/pokemon/{name}"
POKEAPI_MOVE = "https://pokeapi.co/api/v2/move/{name}"
OUTPUT_FILE = Path("dataset.jsonl")
MIN_RATING = 1500
FORMAT = "gen9ou"
MAX_PAGES = 20

pokemon_cache: dict = {}
move_cache: dict = {}


def normalize_name(name: str) -> str:
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "").replace(":", "")


def fetch_pokemon_data(name: str) -> dict:
    key = normalize_name(name)
    if key in pokemon_cache:
        return pokemon_cache[key]

    try:
        r = requests.get(POKEAPI_POKEMON.format(name=key), timeout=10)
        if r.status_code == 404:
            # try base form (e.g. "landorus-therian" -> "landorus")
            base = key.split("-")[0]
            r = requests.get(POKEAPI_POKEMON.format(name=base), timeout=10)
        r.raise_for_status()
        data = r.json()
        stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
        result = {
            "types": [t["type"]["name"] for t in data["types"]],
            "hp": stats.get("hp", "?"),
            "atk": stats.get("attack", "?"),
            "def": stats.get("defense", "?"),
            "spa": stats.get("special-attack", "?"),
            "spd": stats.get("special-defense", "?"),
            "spe": stats.get("speed", "?"),
        }
    except Exception:
        result = {"types": [], "hp": "?", "atk": "?", "def": "?", "spa": "?", "spd": "?", "spe": "?"}

    pokemon_cache[key] = result
    return result


def fetch_move_data(name: str) -> dict:
    key = normalize_name(name)
    if key in move_cache:
        return move_cache[key]

    try:
        r = requests.get(POKEAPI_MOVE.format(name=key), timeout=10)
        r.raise_for_status()
        data = r.json()
        result = {
            "type": data["type"]["name"],
            "power": data["power"] or 0,
            "accuracy": data["accuracy"] or 100,
            "category": data["damage_class"]["name"],
        }
    except Exception:
        result = {"type": "?", "power": "?", "accuracy": "?", "category": "?"}

    move_cache[key] = result
    return result


def fetch_replay_ids(page: int) -> list[str]:
    params = {"format": FORMAT, "rating": MIN_RATING, "page": page}
    r = requests.get(REPLAY_SEARCH_URL, params=params, timeout=10)
    r.raise_for_status()
    return [replay["id"] for replay in r.json()]


def fetch_replay(replay_id: str) -> dict:
    r = requests.get(REPLAY_URL.format(id=replay_id), timeout=10)
    r.raise_for_status()
    return r.json()


def parse_replay(replay: dict) -> list[dict]:
    log = replay.get("log", "")
    winner = None
    samples = []
    lines = log.split("\n")

    for line in lines:
        if line.startswith("|win|"):
            winner = line.split("|")[2].strip()
            break

    if not winner:
        return []

    p1 = replay.get("p1", "")
    winner_slot = "p1" if winner == p1 else "p2"
    opp_slot = "p2" if winner_slot == "p1" else "p1"

    current_turn = 0
    active = {}
    hp = {}
    status = {}
    weather = "none"
    moves_seen: dict[str, list[str]] = {"p1": [], "p2": []}

    for line in lines:
        parts = line.split("|")
        if len(parts) < 2:
            continue

        tag = parts[1]

        if tag == "turn":
            current_turn = int(parts[2])

        elif tag == "switch":
            player = parts[2][:2]
            pokemon = parts[3].split(",")[0].strip()
            active[player] = pokemon
            hp[pokemon] = parts[4].strip() if len(parts) > 4 else "100/100"
            status[pokemon] = "healthy"

        elif tag in ("-damage", "-heal"):
            pokemon = parts[2].split(": ")[-1]
            hp_val = parts[3].strip() if len(parts) > 3 else "?"
            # strip status from hp string e.g. "45/100 brn"
            hp[pokemon] = hp_val.split(" ")[0]

        elif tag == "-status":
            pokemon = parts[2].split(": ")[-1]
            status[pokemon] = parts[3].strip() if len(parts) > 3 else "?"

        elif tag == "-curestatus":
            pokemon = parts[2].split(": ")[-1]
            status[pokemon] = "healthy"

        elif tag == "-weather":
            weather = parts[2].strip() if len(parts) > 2 else "none"
            if weather == "none":
                weather = "none"

        elif tag == "move":
            player = parts[2][:2]
            move = parts[3].strip()

            if move not in moves_seen[player]:
                moves_seen[player].append(move)

            if player != winner_slot or not active:
                continue

            my_pokemon = active.get(winner_slot, "?")
            opp_pokemon = active.get(opp_slot, "?")

            my_data = fetch_pokemon_data(my_pokemon)
            opp_data = fetch_pokemon_data(opp_pokemon)
            move_data = fetch_move_data(move)

            my_hp = hp.get(my_pokemon, "?")
            opp_hp = hp.get(opp_pokemon, "?")
            my_status = status.get(my_pokemon, "healthy")
            opp_status = status.get(opp_pokemon, "healthy")

            opp_moves = moves_seen[opp_slot]

            my_types = "/".join(my_data["types"]) if my_data["types"] else "?"
            opp_types = "/".join(opp_data["types"]) if opp_data["types"] else "?"

            opp_moves_str = ""
            if opp_moves:
                move_details = []
                for m in opp_moves[-4:]:
                    md = fetch_move_data(m)
                    move_details.append(f"{m} ({md['type']}, {md['power']}pw, {md['category']})")
                opp_moves_str = f" | Moves seen: {', '.join(move_details)}"

            prompt = (
                f"Turn {current_turn}. Weather: {weather}. "
                f"Your pokemon: {my_pokemon} ({my_hp} HP, {my_status}) | "
                f"Type: {my_types} | Atk: {my_data['atk']} SpA: {my_data['spa']} Spe: {my_data['spe']}. "
                f"Opponent: {opp_pokemon} ({opp_hp} HP, {opp_status}) | "
                f"Type: {opp_types} | Def: {opp_data['def']} SpD: {opp_data['spd']} Spe: {opp_data['spe']}"
                f"{opp_moves_str}. "
                f"What move do you use?"
            )

            completion = f"{move} ({move_data['type']}, {move_data['power']}pw, {move_data['category']})"

            samples.append({"prompt": prompt, "completion": completion})

    return samples


def main():
    all_samples = []
    seen_ids = set()

    print(f"Scraping {MAX_PAGES} pages of {FORMAT} replays (rating >= {MIN_RATING})...")

    for page in range(1, MAX_PAGES + 1):
        print(f"Page {page}/{MAX_PAGES}...")
        try:
            ids = fetch_replay_ids(page)
            if not ids:
                print("No more replays.")
                break

            for replay_id in ids:
                if replay_id in seen_ids:
                    continue
                seen_ids.add(replay_id)

                try:
                    replay = fetch_replay(replay_id)
                    samples = parse_replay(replay)
                    all_samples.extend(samples)
                    print(f"  {replay_id}: {len(samples)} samples")
                except Exception as e:
                    print(f"  {replay_id}: error - {e}")

                time.sleep(0.3)

        except Exception as e:
            print(f"Page {page} error: {e}")

        time.sleep(0.5)

    print(f"\nTotal samples: {len(all_samples)}")

    with open(OUTPUT_FILE, "w") as f:
        for sample in all_samples:
            f.write(json.dumps(sample) + "\n")

    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
