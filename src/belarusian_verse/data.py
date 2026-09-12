"""Where the Belarusian tables come from.

By default they are downloaded once from the Hugging Face dataset and cached there:
https://huggingface.co/datasets/YauhenBichel/belarusian-verse (CC BY-SA 4.0, from GrammarDB).

Point BELARUSIAN_VERSE_DATA at a folder holding the same files to work offline, or pass an
explicit path to any of the load_* functions.
"""
import os

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
    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:  # keep the failure readable
        raise ImportError(
            "the tables are downloaded with huggingface_hub: pip install huggingface_hub, "
            f"or set BELARUSIAN_VERSE_DATA to a folder containing {relative}") from exc
    return hf_hub_download(DATASET, relative, repo_type="dataset")
