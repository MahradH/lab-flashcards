"""IPA -> standard Persian phonetic spelling.

Used to (re)generate the ``pron`` field of the flashcards. The IPA comes
from espeak-ng (en-us). Every English sound gets one fixed Persian
spelling, so a word always looks the same wherever it appears:

  vowels      /iː/ ی (ای at the start), /ɪ e ə/ ِ (اِ at the start),
              /æ/ َ, /ʌ ɑː ɔː/ ا, /oʊ uː ʊ/ و, /eɪ/ ِی, /aɪ/ ای,
              /aʊ/ او, /ɔɪ/ وی, /ɜː ɝ ɚ/ ِر
  consonants  θ ث, ð ذ, ʃ ش, ʒ ژ, tʃ چ, dʒ ج, ŋ نگ (ن before k/g), ...
"""
import re
import subprocess

# pattern -> (word-initial form, form after a consonant)
VOWELS = {
    "iː": ("ای", "ی"),
    "ɪ": ("اِ", "ِ"),
    "e": ("اِ", "ِ"),
    "ɛ": ("اِ", "ِ"),
    "ə": ("اِ", "ِ"),
    "ɐ": ("اِ", "ِ"),
    "ᵻ": ("اِ", "ِ"),
    "ᵿ": ("اُ", "ُ"),
    "æ": ("اَ", "َ"),
    "ʌ": ("آ", "ا"),
    "ɑː": ("آ", "ا"),
    "ɒ": ("آ", "ا"),
    "ɔː": ("آ", "ا"),
    "ɔ": ("آ", "ا"),
    "ɜː": ("اِر", "ِر"),
    "ɝ": ("اِر", "ِر"),
    "ɚ": ("اِر", "ِر"),
    "oʊ": ("او", "و"),
    "o": ("او", "و"),
    "uː": ("او", "و"),
    "ʊ": ("او", "و"),
    "u": ("او", "و"),
    "aɪ": ("آی", "ای"),
    "aʊ": ("آو", "او"),
    "ɔɪ": ("اوی", "وی"),
    "eɪ": ("اِی", "ِی"),
    "i": ("ای", "ی"),
}

CONSONANTS = [
    ("tʃ", "چ"),
    ("dʒ", "ج"),
    ("ʃ", "ش"),
    ("ʒ", "ژ"),
    ("θ", "ث"),
    ("ð", "ذ"),
    ("ŋ", "نگ"),
    ("ɹ", "ر"),
    ("ɾ", "ت"),  # American flapped t (water, little)
    ("j", "ی"),
    ("w", "و"),
    ("x", "خ"),
    ("ç", "ه"),
    ("ʔ", ""),
    ("p", "پ"),
    ("b", "ب"),
    ("t", "ت"),
    ("d", "د"),
    ("k", "ک"),
    ("ɡ", "گ"),
    ("g", "گ"),
    ("f", "ف"),
    ("v", "و"),
    ("s", "س"),
    ("z", "ز"),
    ("m", "م"),
    ("n", "ن"),
    ("l", "ل"),
    ("r", "ر"),
    ("h", "ه"),
]

_VOWEL_KEYS = sorted(VOWELS, key=len, reverse=True)
_RHOTIC = {"ɜː", "ɝ", "ɚ"}


def _ends_vowel(out):
    return bool(out) and out[-1][-1] in "اآوی"

# Words espeak-ng transcribes oddly or that need a convention of their own.
OVERRIDES = {
    "the": "ذِ",
    "a": "اِ",
    "of": "اُو",
    "colonel": "کِرنِل",
    "queue": "کیو",
    "entrepreneur": "آنترِپرِنِر",
}


def ipa_to_fa(ipa):
    ipa = ipa.replace("\u200d", "").replace("ˈ", "").replace("ˌ", "")
    out = []
    after_cons = False
    i = 0
    while i < len(ipa):
        hit = False
        for key in _VOWEL_KEYS:
            if ipa.startswith(key, i):
                full, bare = VOWELS[key]
                # r-coloured vowel directly after an r is already spelled
                if key in _RHOTIC and out and out[-1].endswith("ر"):
                    pass
                else:
                    # a vowel that follows another vowel never gets a
                    # fresh alef (giant -> جایِنت, not جایاِنت)
                    out.append(bare if (after_cons or _ends_vowel(out)) else full)
                after_cons = False
                i += len(key)
                hit = True
                break
        if hit:
            continue
        for pat, rep in CONSONANTS:
            if ipa.startswith(pat, i):
                if pat == "ŋ" and i + 1 < len(ipa) and ipa[i + 1] in "kgɡ":
                    rep = "ن"
                if rep:
                    out.append(rep)
                after_cons = bool(rep)
                i += len(pat)
                hit = True
                break
        if hit:
            continue
        i += 1
    s = "".join(out)
    # no doubled letters from joined letters ("کارری")
    for d in ("رر", "لل", "نن", "زز", "ژژ", "تت", "دت"):
        s = s.replace(d, d[0])
    return s


def _espeak(word):
    try:
        p = subprocess.run(
            ["espeak-ng", "-v", "en-us", "-q", "--ipa=3", word],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return p.stdout.strip()
    except Exception:
        return ""


def pron(word):
    """Persian phonetic spelling of an English word or phrase."""
    pieces = []
    for w in re.findall(r"[A-Za-z'’]+", word):
        if not w:
            continue
        low = w.lower()
        if low in OVERRIDES:
            pieces.append(OVERRIDES[low])
            continue
        ipa = _espeak(w)
        if not ipa:
            continue
        fa = ipa_to_fa(ipa)
        if fa:
            pieces.append(fa)
    return " ".join(p for p in pieces if p)
