#!/usr/bin/env python3

import argparse
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

API_ENDPOINT = "https://en.wikipedia.org/w/api.php"


STOPWORDS = {
    "a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at",
    "be","because","been","before","being","below","between","both","but","by",
    "can","can't","cannot","could","couldn't",
    "did","didn't","do","does","doesn't","doing","don't","down","during",
    "each",
    "few","for","from","further",
    "had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here",
    "here's","hers","herself","him","himself","his","how","how's",
    "i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself",
    "let's",
    "me","more","most","mustn't","my","myself",
    "no","nor","not",
    "of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own",
    "same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such",
    "than","that","that's","the","their","theirs","them","themselves","then","there","there's","these",
    "they","they'd","they'll","they're","they've","this","those","through","to","too",
    "under","until","up",
    "very",
    "was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when",
    "when's","where","where's","which","while","who","who's","whom","why","why's","with","won't",
    "would","wouldn't",
    "you","you'd","you'll","you're","you've","your","yours","yourself","yourselves",
}


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "wikipedia_analysis/1.0 (category_wordfreq.py)"})

    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.8,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


_SESSION = _make_session()


def _http_get_json(params: Dict[str, str]) -> Dict:
    resp = _SESSION.get(API_ENDPOINT, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _normalize_category(category: str) -> str:
    if category.startswith("Category:"):
        return category[len("Category:") :]
    return category


def _cache_file_for_category(category: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", _normalize_category(category).strip()) or "_"
    return Path(__file__).resolve().parent / ".cache" / f"category_{safe}.json"


def _load_cached_counts(category: str) -> Counter[str] | None:
    cache_file = _cache_file_for_category(category)
    try:
        data = json.loads(cache_file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except Exception:
        return None

    counts = data.get("counts")
    if not isinstance(counts, dict):
        return None

    out: Counter[str] = Counter()
    for k, v in counts.items():
        if isinstance(k, str) and isinstance(v, int):
            out[k] = v
    return out


def _save_cached_counts(category: str, counts: Counter[str]) -> None:
    cache_file = _cache_file_for_category(category)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "category": _normalize_category(category),
        "created_at": time.time(),
        "total_words": int(sum(counts.values())),
        "counts": dict(counts),
    }
    tmp = cache_file.with_suffix(cache_file.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    os.replace(tmp, cache_file)


def iter_category_pages(category: str) -> Iterable[Tuple[int, str]]:
    cmtitle = category
    if not cmtitle.startswith("Category:"):
        cmtitle = f"Category:{cmtitle}"

    cmcontinue: str | None = None
    while True:
        params = {
            "action": "query",
            "format": "json",
            "list": "categorymembers",
            "cmtitle": cmtitle,
            "cmtype": "page",
            "cmlimit": "500",
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        data = _http_get_json(params)
        members = data.get("query", {}).get("categorymembers", [])
        for m in members:
            yield int(m["pageid"]), str(m["title"])

        cmcontinue = data.get("continue", {}).get("cmcontinue")
        if not cmcontinue:
            break


def fetch_plaintext_extracts(pageids: List[int]) -> Dict[int, str]:
    if not pageids:
        return {}

    # Conservative batching. MediaWiki limits vary by prop and user rights.
    batch_size = 20
    out: Dict[int, str] = {}

    for i in range(0, len(pageids), batch_size):
        batch = pageids[i : i + batch_size]
        params = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "extracts",
            "explaintext": "1",
            "exsectionformat": "plain",
            "pageids": "|".join(map(str, batch)),
        }
        data = _http_get_json(params)
        pages = data.get("query", {}).get("pages", [])
        for p in pages:
            pid = int(p["pageid"])
            out[pid] = str(p.get("extract", ""))

    return out


_WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


def tokenize(text: str) -> Iterable[str]:
    for m in _WORD_RE.finditer(text):
        w = m.group(0).lower()
        w = w.strip("'")
        if not w:
            continue
        yield w


def is_non_common(word: str) -> bool:
    if word in STOPWORDS:
        return False
    if len(word) <= 2:
        return False
    return True


def format_table(rows: List[Tuple[str, int]], total: int) -> str:
    lines = ["rank\tword\tcount\tcum_count\tcum_pct"]
    cum = 0
    for idx, (w, c) in enumerate(rows, start=1):
        cum += c
        pct = (cum / total * 100.0) if total else 0.0
        lines.append(f"{idx}\t{w}\t{c}\t{cum}\t{pct:.4f}")
    return "\n".join(lines)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Compute cumulative frequency of non-common words across all pages in a Wikipedia category "
            "using the MediaWiki API."
        )
    )
    ap.add_argument("category", help="Category name (with or without 'Category:' prefix). Example: Large_language_models")
    ap.add_argument("--top", type=int, default=0, help="If >0, only print the top N words (still cumulative over those rows).")
    ap.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between API calls (politeness).")
    ap.add_argument("--refresh", action="store_true", help="Recompute results instead of using cached output")
    args = ap.parse_args(argv)

    counts: Counter[str] | None = None
    if not args.refresh:
        counts = _load_cached_counts(args.category)

    if counts is None:
        pageids: List[int] = []
        for pid, _title in iter_category_pages(args.category):
            pageids.append(pid)

        if not pageids:
            print("No pages found for category.", file=sys.stderr)
            return 2

        counts = Counter()

        # Fetch content in batches
        batch_size = 200
        for i in range(0, len(pageids), batch_size):
            batch = pageids[i : i + batch_size]
            extracts = fetch_plaintext_extracts(batch)
            for text in extracts.values():
                for w in tokenize(text):
                    if is_non_common(w):
                        counts[w] += 1

            if args.sleep > 0:
                time.sleep(args.sleep)

        _save_cached_counts(args.category, counts)

    assert counts is not None
    total = sum(counts.values())
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    if args.top and args.top > 0:
        rows = rows[: args.top]

    print(format_table(rows, total))
    return 0


def get_category_counts(category: str, refresh: bool = False, sleep: float = 0.0) -> Counter[str]:
    counts: Counter[str] | None = None
    if not refresh:
        counts = _load_cached_counts(category)

    if counts is None:
        pageids: List[int] = []
        for pid, _title in iter_category_pages(category):
            pageids.append(pid)

        if not pageids:
            return Counter()

        counts = Counter()

        batch_size = 200
        for i in range(0, len(pageids), batch_size):
            batch = pageids[i : i + batch_size]
            extracts = fetch_plaintext_extracts(batch)
            for text in extracts.values():
                for w in tokenize(text):
                    if is_non_common(w):
                        counts[w] += 1

            if sleep > 0:
                time.sleep(sleep)

        _save_cached_counts(category, counts)

    return counts


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
