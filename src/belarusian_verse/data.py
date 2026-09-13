"""Where the Belarusian tables come from.

By default they are downloaded once from the Hugging Face dataset and cached there:
https://huggingface.co/datasets/YauhenBichel/belarusian-verse (CC BY-SA 4.0, from GrammarDB).

One table is not ours to publish and comes from its own source instead: BelVoice's most frequent
stress of common homographs (LGPL-3.0-or-later), fetched from a pinned commit and checked against
its SHA-256 before it is cached next to the others.

Point BELARUSIAN_VERSE_DATA at a folder holding the same files to work offline, or pass an
explicit path to any of the load_* functions.
"""
import hashlib
import os
import tempfile

DATASET = "YauhenBichel/belarusian-verse"
LOCAL_DIR = os.environ.get("BELARUSIAN_VERSE_DATA")
FILES = {
    "stress": "data/be-stress.tsv.gz",
    "forms": "data/be-forms.tsv.gz",
    "overrides": "data/stress-overrides.tsv",
    "rhymes": "data/be-rhymes.tsv.gz",
    "frequency": "data/be-freq.tsv.gz",
    "hunspell_dic": "data/hunspell/be-official.dic",
    "hunspell_aff": "data/hunspell/be-official.aff",
    "homographs": "belvoice/stresses-stat.json",
}
# Tables that are not in the dataset: name -> (URL at a pinned commit, SHA-256 of that file).
# stresses-stat.json is from BelVoice by Aleś Bułojčyk and contributors, https://github.com/Belarus/BelVoice,
# licensed LGPL-3.0-or-later. It is downloaded at run time and never shipped with this package.
URLS = {
    "homographs": (
        "https://raw.githubusercontent.com/Belarus/BelVoice/60401e614210f8788d13cbfd9df6bb4726845c38/"
        "framework/belvoice/synth/stress/stresses-stat.json",
        "c86aa15ea3ade2d1b48ab39a431637dddedd4ae15dadf94fa8f4d551b66b3393",
    ),
}


def table(name):
    """Path to one table, downloading it on first use."""
    relative = FILES[name]
    if LOCAL_DIR:
        local = os.path.join(LOCAL_DIR, os.path.basename(relative))
        if os.path.exists(local):
            return local
        local = os.path.join(LOCAL_DIR, relative)
        if os.path.exists(local):
            return local
        raise FileNotFoundError(f"{relative} not found under BELARUSIAN_VERSE_DATA={LOCAL_DIR}")
    if name in URLS:
        return _fetch(relative, *URLS[name])
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # keep the failure readable
        raise ImportError(
            "the tables are downloaded with huggingface_hub: pip install huggingface_hub, "
            f"or set BELARUSIAN_VERSE_DATA to a folder containing {relative}") from exc
    return hf_hub_download(DATASET, relative, repo_type="dataset")


def _cache_dir():
    """The Hugging Face cache, so one folder (and one CI cache) holds every table."""
    try:
        from huggingface_hub.constants import HF_HOME
    except ImportError:
        HF_HOME = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
    return os.path.join(HF_HOME, "belarusian-verse")


def _fetch(relative, url, sha256):
    path = os.path.join(_cache_dir(), relative)
    if os.path.exists(path):
        return path
    from urllib.request import urlopen
    with urlopen(url, timeout=30) as response:
        body = response.read()
    if hashlib.sha256(body).hexdigest() != sha256:
        raise ValueError(f"{url} does not match its pinned SHA-256; not cached")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # write beside the target and rename, so an interrupted download never looks like a table
    handle, partial = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".part")
    with os.fdopen(handle, "wb") as fh:
        fh.write(body)
    os.replace(partial, path)
    return path
