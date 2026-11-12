"""Cliente mínimo da API da Riot (lê a chave de app/.env)."""
import json, os, time, urllib.request, urllib.error, urllib.parse
from pathlib import Path

ENV = Path(__file__).with_name(".env")


def _key():
    if os.environ.get("RIOT_API_KEY"):
        return os.environ["RIOT_API_KEY"]
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if line.startswith("RIOT_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("RIOT_API_KEY não encontrada")


REGIONAL = "https://americas.api.riotgames.com"
PLATFORM = "https://br1.api.riotgames.com"


def get(url, params=None, tries=5):
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"X-Riot-Token": _key(),
                                              "User-Agent": "merdavp-ranking"})
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(int(e.headers.get("Retry-After", "5")) + 1)
                continue
            raise
    raise RuntimeError("limite de requisições estourado: " + url)


def account(name, tag):
    return get(f"{REGIONAL}/riot/account/v1/accounts/by-riot-id/"
               f"{urllib.parse.quote(name)}/{urllib.parse.quote(tag)}")


def match_ids(puuid, queue=None, start_time=None, end_time=None, count=100):
    p = {"count": count}
    if queue: p["queue"] = queue
    if start_time: p["startTime"] = int(start_time)
    if end_time: p["endTime"] = int(end_time)
    return get(f"{REGIONAL}/lol/match/v5/matches/by-puuid/{puuid}/ids", p)


def match(match_id):
    return get(f"{REGIONAL}/lol/match/v5/matches/{match_id}")
