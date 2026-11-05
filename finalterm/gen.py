#!/usr/bin/env python3
"""Generate final-term (Units 5-8) flashcard data for data-en2.js."""
import json, re, subprocess, sys

pairs = json.load(open('/tmp/finalterm/pairs2.json'))
NAME = {'Five': 5, 'Six': 6, 'Seven': 7, 'Eight': 8}
TITLE = {
    5: ("Acid test",),
    6: ("Stress: Another chimera",),
    7: ("Why sugar is bad for you",),
    8: ("Malaria: A case study of evolution",),
}
FA_NUM = {5: '۵', 6: '۶', 7: '۷', 8: '۸'}

DROP = {'impat', 'vitat', 'deleted'}
FIX_EN = {'compse': 'compose'}

def clean_fa(fa):
    fa = fa.replace('ـ', '')
    fa = re.sub(r'[()\[\]]', ' ', fa)                 # stray brackets from bidi
    fa = re.sub(r'\s*\d\s*$', '', fa)                 # trailing exercise number
    fa = re.sub(r'\s+[a-d]$', '', fa)                 # trailing answer letter
    fa = re.sub(r'\s*/\s*', ' / ', fa)
    fa = fa.replace('...', '').replace('…', '')
    fa = re.sub(r'^[\u064B-\u0652\s/.,،؛-]+', '', fa)
    fa = re.sub(r'\s+', ' ', fa).strip(' /,-.,،؛')
    return fa

# ---------- pronunciation: espeak IPA -> Persian transliteration ----------
_ZWJ = '‍'
# (pattern, full-letter form, bare form after a consonant)
_VOWELS = {
    'eɪ': ('ی', 'ی'), 'aɪ': ('ی', 'ی'), 'iː': ('ی', 'ی'), 'ɪ': ('ی', 'ی'), 'i': ('ی', 'ی'),
    'ᵻ': ('ی', 'ی'), 'ɛ': ('اِ', 'ِ'), 'e': ('اِ', 'ِ'), 'ə': ('اِ', 'ِ'),
    'æ': ('ا', 'ا'), 'ʌ': ('ا', 'ا'), 'ᵿ': ('اُ', 'ُ'),
    'ɑː': ('آ', 'ا'), 'ɒː': ('اُ', 'ُ'), 'ɔː': ('اُ', 'ُ'), 'oʊ': ('اُ', 'ُ'), 'o': ('اُ', 'ُ'),
    'ɔːɹ': ('اُر', 'ور'),
    'ʊ': ('اُ', 'ُ'), 'uː': ('او', 'و'), 'u': ('او', 'و'),
    'aʊ': ('اَو', 'َو'), 'ɔɪ': ('اُی', 'ُی'),
    'ɜː': ('اِر', 'ِر'), 'ɝ': ('اِر', 'ِر'), 'ɚ': ('اُر', 'ُر'),
}
# w followed by these rounded vowels reads as وا (water, want, wall)
_WA = {'ɔː', 'ɒː', 'ɔ', 'o', 'ɔːɹ'}
_CONS = [
    ('tʃ', 'چ'), ('dʒ', 'ج'), ('ʃ', 'ش'), ('ʒ', 'ژ'), ('θ', 'س'), ('ð', 'ذ'),
    ('ŋ', 'نگ'), ('ɹ', 'ر'), ('ɾ', 'ت'), ('j', 'ی'), ('x', 'خ'), ('ʔ', ''),
    ('w', 'و'), ('k', 'ک'), ('ks', 'کس'), ('s', 'س'), ('z', 'ز'), ('f', 'ف'), ('v', 'و'), ('p', 'پ'),
    ('b', 'ب'), ('t', 'ت'), ('d', 'د'), ('ɡ', 'گ'), ('g', 'گ'), ('l', 'ل'),
    ('r', 'ر'), ('m', 'م'), ('n', 'ن'), ('h', 'ه'), ('ç', 'ه'),
]
_FULL = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآ')

def ipa_to_fa(ipa):
    ipa = ipa.replace(_ZWJ, '').replace('ˈ', '').replace('ˌ', '')
    out = []
    last = ''          # last emitted full letter
    first_vowel = None # did the word start with a vowel sound?
    pending_bare = None  # (index, full_form) of a trailing bare vowel
    i = 0
    while i < len(ipa):
        # 'w' + rounded vowel -> وا
        if ipa.startswith('w', i):
            rest = ipa[i + 1:]
            matched = False
            for v in sorted(_WA, key=len, reverse=True):
                if rest.startswith(v):
                    out.append('وا'); last = 'ا'; i += 1 + len(v)
                    if first_vowel is None: first_vowel = False
                    matched = True; break
            if matched: continue
        hit = False
        for pat, (full, bare) in sorted(_VOWELS.items(), key=lambda x: -len(x[0])):
            if ipa.startswith(pat, i):
                if last and last in _FULL:
                    out.append(bare)
                    pending_bare = (len(out) - 1, full)
                else:
                    out.append(full)
                    pending_bare = None
                    if first_vowel is None: first_vowel = True
                last = out[-1][-1] if out[-1] else last
                i += len(pat); hit = True; break
        if hit: continue
        for pat, rep in _CONS:
            if ipa.startswith(pat, i):
                out.append(rep)
                pending_bare = None
                if first_vowel is None: first_vowel = False
                last = rep if rep else last
                i += len(pat); hit = True; break
        if hit: continue
        i += 1
    # a word must not end on a dangling diacritic -> promote to full form
    if pending_bare is not None and pending_bare[0] == len(out) - 1:
        out[pending_bare[0]] = pending_bare[1].rstrip('َُِ') or 'ا'
    s = ''.join(out)
    # collapse accidental doubles
    for d in ('رر', 'ژژ', 'زز', 'نن'):
        s = s.replace(d, d[0])
    # final -ə after ت/د reads as ر (water -> واتر, computer -> کامپیوتر)
    s = re.sub(r'([تد])ِ$', r'\1ر', s)
    # word-initial vowel gets an alef
    if first_vowel and s and s[0] not in 'اآ':
        s = 'ا' + s
    s = re.sub(r'^[ِ\u0650]', 'اِ', s)
    s = re.sub(r'^[َ]', 'ا', s)
    s = re.sub(r'^[ُ]', 'اُ', s)
    return s

_cache = {}
def pronounce(word):
    key = word.lower()
    if key in _cache:
        return _cache[key]
    parts = []
    for w in re.findall(r"[A-Za-z'’\-]+", word):
        w = w.strip("-'")
        if not w:
            continue
        try:
            ipa = subprocess.run(
                ['espeak-ng', '-v', 'en-us', '-q', '--ipa=3', w],
                capture_output=True, text=True, timeout=5).stdout.strip()
        except Exception:
            ipa = ''
        parts.append(ipa_to_fa(ipa) if ipa else '')
    res = ' '.join(p for p in parts if p)
    _cache[key] = res
    return res

# ---------- difficulty calibration against existing labels ----------
existing = []
for fn in ('/home/mahradh/Documents/lab-flashcards/data.js',
           '/home/mahradh/Documents/lab-flashcards/data-en2.js'):
    txt = open(fn, encoding='utf-8').read()
    for m in re.finditer(r'en: "([^"]+)", pron: "[^"]*", fa: "[^"]*", difficulty: "(hard|easy)"', txt):
        existing.append((m.group(1), m.group(2)))
print('existing labeled words:', len(existing), file=sys.stderr)

def make_heuristic(thresh, suf_thresh):
    def h(en):
        w = en.lower()
        if ' ' in w: return 'hard'
        if len(w) >= thresh: return 'hard'
        if len(w) >= suf_thresh and re.search(r'(tion|sion|ment|ness|ity|ance|ence|ous|ial|ify|iz)', w):
            return 'hard'
        return 'easy'
    return h

best = None
for thresh in range(8, 13):
    for suf in range(5, 10):
        h = make_heuristic(thresh, suf)
        hits = sum(1 for en, lab in existing if h(en) == lab)
        hard_rate = sum(1 for en, lab in existing if h(en) == 'hard') / len(existing)
        # target ~30% hard like the original data
        score = hits - 400 * abs(hard_rate - 0.29)
        if best is None or score > best[0]:
            best = (score, thresh, suf, hits, hard_rate)
print('best heuristic: len>=%d or suffix(len>=%d): agreement %.1f%%, hard rate %.0f%%'
      % (best[1], best[2], 100 * best[3] / len(existing), 100 * best[4]), file=sys.stderr)
heuristic = make_heuristic(best[1], best[2])

# ---------- build units ----------
blocks = {}
for ukey, unit in NAME.items():
    n = NAME[ukey]
    seen = set()
    words = []
    for en, fa in pairs[ukey]:
        en = FIX_EN.get(en.lower(), en).strip()
        fa = clean_fa(fa)
        if en.lower() in DROP: continue
        if not fa or not re.search(r'[؀-ۿ]', fa): continue
        if len(fa) > 65: continue
        if re.search(r'[A-Za-z]{2,}', fa): continue   # leftover latin in meaning
        k = en.lower()
        if k in seen: continue
        seen.add(k)
        words.append({'en': en, 'pron': pronounce(en), 'fa': fa,
                      'difficulty': heuristic(en)})
    hard = sum(1 for w in words if w['difficulty'] == 'hard')
    print(f'u{n}: {len(words)} words, {hard} hard ({100*hard/max(1,len(words)):.0f}%)', file=sys.stderr)
    blocks[f'u{n}'] = (TITLE[n][0], words)

# ---------- emit JS ----------
FA_DIGIT = {5: '۵', 6: '۶', 7: '۷', 8: '۸'}
lines = []
for key in ('u5', 'u6', 'u7', 'u8'):
    short, words = blocks[key]
    lines.append(f'    {key}: {{')
    lines.append(f'        title: "فصل {FA_DIGIT[int(key[1:])]} — {short}",')
    lines.append(f'        short: "{short}",')
    lines.append('        words: [')
    for w in words:
        en = w['en'].replace('\\', '\\\\').replace('"', '\\"')
        fa = w['fa'].replace('\\', '\\\\').replace('"', '\\"')
        pr = w['pron'].replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'            {{ en: "{en}", pron: "{pr}", fa: "{fa}", difficulty: "{w["difficulty"]}" }},')
    lines.append('        ],')
    lines.append('    },')
open('/tmp/finalterm/units5-8.js', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
print('wrote /tmp/finalterm/units5-8.js', file=sys.stderr)
# sample for review
for key in ('u5', 'u8'):
    print(f'--- {key} sample ---', file=sys.stderr)
    for w in blocks[key][1][:10]:
        print(f"  {w['en']} | {w['pron']} | {w['fa']} | {w['difficulty']}", file=sys.stderr)
