"""Inventory raw Unicode coverage, not browser fallback behavior.

Published Markdown bodies plus visible metadata, and library JSON string values.
Counts overlap neither normalized forms nor source roots; NFC/NFD are diagnostics.
Library includes translations and source scripts, not only Jost body text.
"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import tomllib
import unicodedata as ud

from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
LOCALES = {'de', 'es', 'fr', 'he', 'ja', 'ko', 'ru', 'zh', 'zh-Hant'}


def category(ch):
    name = ud.name(ch, '')
    cp = ord(ch)
    if 'LATIN' in name:
        return 'latin'
    if 0x300 <= cp <= 0x36F:
        return 'combining-mark'
    if 0x2B0 <= cp <= 0x2FF:
        return 'modifier'
    for script in ('GREEK', 'HEBREW', 'CYRILLIC', 'ARABIC', 'CUNEIFORM', 'DEVANAGARI', 'UGARITIC'):
        if script in name:
            return script.lower()
    if any(s in name for s in ('CJK', 'HIRAGANA', 'KATAKANA', 'HANGUL', 'IDEOGRAPH')):
        return 'east-asian'
    return 'other'


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in {'url', 'href', 'id', 'refId', 'audio', 'path', 'slug', 'bookSlug'}:
                yield from strings(item)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, required=True)
    args = parser.parse_args()
    fonts = {key: TTFont(ROOT / 'upstream' / path).getBestCmap()
             for key, path in [('original', 'site-original.woff2'), ('upstream', 'Jost-Roman.ttf')]}
    counts = Counter()
    scopes = defaultdict(Counter)
    examples = defaultdict(set)
    files = Counter()
    sequences = Counter()
    skipped_drafts = 0

    def consume(text, path, scope):
        files[scope] += 1
        for ch, n in Counter(text).items():
            if ord(ch) < 128 or ch.isspace():
                continue
            counts[ch] += n
            scopes[ch][scope] += n
            if len(examples[ch]) < 5:
                examples[ch].add(path)
        sequences.update(re.findall(r'[^\W\d_][\u0300-\u036f]+', text))

    for path in sorted((args.site / 'content').rglob('*.md')):
        raw = path.read_text()
        meta = {}
        body = raw
        if raw.startswith('+++'):
            _, front, body = raw.split('+++', 2)
            meta = tomllib.loads(front)
        if meta.get('draft'):
            skipped_drafts += 1
            continue
        rel = path.relative_to(args.site)
        lang = rel.parts[1] if rel.parts[1] in LOCALES else 'en'
        # Markdown source audit: shortcode arguments count; code and URLs do not.
        body = re.sub(r'```.*?```', '', body, flags=re.S)
        body = re.sub(r'https?://[^\s)<>\"]+', '', body)
        visible = '\n'.join(str(meta.get(k, '')) for k in ('title', 'description'))
        consume(visible + '\n' + body, rel.as_posix(), f'markdown:{lang}')
    for path in sorted((args.site / 'data/library').rglob('*.json')):
        rel = path.relative_to(args.site)
        if any(p in {'reviews', 'curation', 'audioplay', 'alignment'} for p in rel.parts):
            continue
        consume('\n'.join(strings(json.loads(path.read_text()))), rel.as_posix(), 'library-json')
    rows = []
    for ch, n in sorted(counts.items(), key=lambda item: (-item[1], ord(item[0]))):
        rows.append({'character': ch, 'codepoint': f'U+{ord(ch):04X}',
                     'name': ud.name(ch, 'UNNAMED'), 'category': category(ch),
                     'count': n, 'scopes': dict(scopes[ch]), 'examples': sorted(examples[ch]),
                     'original': ord(ch) in fonts['original'], 'upstream': ord(ch) in fonts['upstream'],
                     'nfc': ud.normalize('NFC', ch), 'nfd': ud.normalize('NFD', ch)})
    result = {'method': __doc__, 'files': dict(files), 'skipped_drafts': skipped_drafts,
              'characters': rows, 'combining_sequences': dict(sequences.most_common())}
    (ROOT / 'audit/coverage.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    scholarly = [r for r in rows if r['category'] in {'latin', 'modifier', 'combining-mark'} and not r['original']]
    lines = ['# Corpus coverage audit', '',
             'Source: published Markdown and library JSON in the local website checkout.',
             'Counts describe source text, not measured browser fallback; library text also uses other fonts.',
             'Draft Markdown is excluded. JSON translation strings are included; review/curation/audio directories are excluded.',
             'No content prose is copied into this report. Paths identify examples.', '',
             f'Files: {dict(files)}. Draft Markdown skipped: {skipped_drafts}.', '',
             '## Latin, modifiers, and combining marks missing from the old site font', '',
             '| Character | Codepoint | Name | Occurrences | Full Jost |',
             '|---|---|---|---:|---|']
    for r in scholarly:
        lines.append(f"| {r['character']} | {r['codepoint']} | {r['name']} | {r['count']} | {'yes' if r['upstream'] else 'missing'} |")
    lines += ['', '## Other scripts', '',
              'Greek, Hebrew, cuneiform, Arabic, Indic and East Asian characters remain separate script-font responsibilities.',
              'The JSON inventory retains every non-ASCII character and up to five example paths per character.',
              'A cmap presence check does not prove combining-mark positioning or a particular CSS font choice.', '']
    (ROOT / 'audit/README.md').write_text('\n'.join(lines))
    print(f'{len(rows)} distinct non-ASCII characters; {len(scholarly)} Latin/mark gaps in old site font')


if __name__ == '__main__':
    main()
