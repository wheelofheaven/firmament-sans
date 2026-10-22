"""Check shaping, coverage, names, kerning retention and reproducible artifacts."""
from io import BytesIO
import json
from pathlib import Path
import unicodedata as ud

from fontTools.ttLib import TTFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parents[1]


def shape(path, text, features=None):
    font = hb.Font(hb.Face(path.read_bytes()))
    buffer = hb.Buffer()
    buffer.add_str(text)
    buffer.guess_segment_properties()
    hb.shape(font, buffer, features)
    return [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
            for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]


def main():
    report = {}
    for path in sorted((ROOT/'fonts').glob('FirmamentSans-*.ttf')):
        font = TTFont(path)
        cmap = font.getBestCmap()
        for ch in 'āēīōūšḥṣṭḫṃḍṛṇṯḇḏḵḡḷṝḹṉṟṅṁḳḻḗṓṗẓʾʿə':
            assert ord(ch) in cmap, (path.name, ch)
            if ch.islower() and len(ch.upper()) == 1:
                assert ord(ch.upper()) in cmap, (path.name, ch.upper())
        assert font['name'].getDebugName(1) == 'Firmament Sans'
        bold = 'Bold' in path.stem
        italic = 'Italic' in path.stem
        assert bool(font['OS/2'].fsSelection & 32) == bold
        assert bool(font['OS/2'].fsSelection & 1) == italic
        assert bool(font['head'].macStyle & 1) == bold
        assert bool(font['head'].macStyle & 2) == italic
        assert 'fvar' not in font
        features = {r.FeatureTag for r in font['GPOS'].table.FeatureList.FeatureRecord}
        assert {'kern', 'mark'} <= features
        # Every added composite must shape identically from canonical NFD.
        additions = json.loads((ROOT/'audit/build.json').read_text())[font['name'].getDebugName(2)]['added']
        for ch in additions.values():
            if ud.normalize('NFD', ch) != ch:
                assert shape(path, ch) == shape(path, ud.normalize('NFD', ch)), (path.name, ch)
        for text in ['ʾĕlōhīm šāmayim ḥayyīm', 'ḫ ṯ ḇ ḏ ḵ ṛ ṝ Ṃ', 'Ḥ Ṣ Ṭ Ḫ ʿ ə']:
            assert all(g[0] != 0 for g in shape(path, text)), (path.name, text)
        # q + below dot has no precomposed letter: this exercises GPOS directly.
        combined = shape(path, 'q\u0323')
        assert len(combined) == 2 and combined[1][1] == 0 and combined[1][3] != 0
        original = TTFont(ROOT/'fonts'/path.name.replace('FirmamentSans-', 'Jost-').replace('.ttf', '.woff2'))
        original.flavor = None
        buf = BytesIO()
        original.save(buf)
        reference = hb.Font(hb.Face(buf.getvalue()))
        for text in ['AVATAR To Wa', 'The heavens and the earth.', 'ā ē ī ō ū š', 'Привет мир']:
            buffer = hb.Buffer(); buffer.add_str(text); buffer.guess_segment_properties()
            hb.shape(reference, buffer)
            expected = [(i.codepoint, p.x_advance, p.y_advance, p.x_offset, p.y_offset)
                        for i, p in zip(buffer.glyph_infos, buffer.glyph_positions)]
            assert shape(path, text) == expected, (path.name, text, 'upstream regression')
        web = TTFont(path.with_suffix('.woff2'))
        assert web.getBestCmap() == cmap
        report[path.name] = {'codepoints': len(cmap), 'shaping': 'passed', 'upstream_regressions': 'passed', 'bytes_woff2': path.with_suffix('.woff2').stat().st_size}
    (ROOT/'audit/validation.json').write_text(json.dumps(report, indent=2)+'\n')
    corpus = json.loads((ROOT/'audit/coverage.json').read_text())
    cmap = TTFont(ROOT/'fonts/FirmamentSans-Regular.ttf').getBestCmap()
    remaining = [r for r in corpus['characters'] if r['category'] in {'latin', 'modifier', 'combining-mark'} and ord(r['character']) not in cmap]
    (ROOT/'audit/remaining.json').write_text(json.dumps(remaining, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
