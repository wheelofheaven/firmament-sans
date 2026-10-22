"""Build the static scholarly pilot from pinned Jost variable inputs.

All added outlines derive from Jost components; the half rings are new curves.
Existing Jost outlines, layout tables and hinting survive instantiation.
The pilot intentionally does not claim a variable-font extension.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata as ud

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

ROOT = Path(__file__).resolve().parents[1]
FAMILY = 'Firmament Sans'


def bounds(font, name):
    glyph = font['glyf'][name]
    glyph.recalcBounds(font['glyf'])
    return glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax


def component(font, pieces):
    pen = TTGlyphPen(font.getGlyphSet())
    for name, transform in pieces:
        pen.addComponent(name, transform)
    return pen.glyph()


def install(font, name, glyph, advance, cp=None):
    font['glyf'][name] = glyph
    font['hmtx'][name] = (advance, 0)
    glyph.recalcBounds(font['glyf'])
    font['hmtx'][name] = (advance, getattr(glyph, 'xMin', 0))
    order = font.getGlyphOrder()
    font.setGlyphOrder(order if name in order else order + [name])
    if cp is not None:
        for table in font['cmap'].tables:
            if table.isUnicode() and table.format in (4, 12):
                table.cmap[cp] = name


def merge_mark_layout(font, feature_text):
    """Compile new lookups separately; preserve upstream kerning and features."""
    scratch = deepcopy(font)
    addOpenTypeFeaturesFromString(scratch, feature_text, tables={'GPOS'})
    old = font['GPOS'].table
    new = scratch['GPOS'].table
    lookup_offset = len(old.LookupList.Lookup)
    feature_offset = len(old.FeatureList.FeatureRecord)
    old.LookupList.Lookup.extend(new.LookupList.Lookup)
    old.LookupList.LookupCount = len(old.LookupList.Lookup)
    for record in new.FeatureList.FeatureRecord:
        record.Feature.LookupListIndex = [i + lookup_offset for i in record.Feature.LookupListIndex]
        old.FeatureList.FeatureRecord.append(record)
    old.FeatureList.FeatureCount = len(old.FeatureList.FeatureRecord)
    # Attach to Latin and default shaping; other scripts retain their layout.
    for record in new.ScriptList.ScriptRecord:
        for lang in [record.Script.DefaultLangSys] + [r.LangSys for r in record.Script.LangSysRecord]:
            if lang:
                lang.FeatureIndex = [i + feature_offset for i in lang.FeatureIndex]
        existing = next((r for r in old.ScriptList.ScriptRecord if r.ScriptTag == record.ScriptTag), None)
        if existing:
            indices = record.Script.DefaultLangSys.FeatureIndex
            for lang in [existing.Script.DefaultLangSys] + [r.LangSys for r in existing.Script.LangSysRecord]:
                if lang:
                    lang.FeatureIndex += indices
                    lang.FeatureCount = len(lang.FeatureIndex)
        else:
            old.ScriptList.ScriptRecord.append(record)
    old.ScriptList.ScriptRecord.sort(key=lambda r: r.ScriptTag)
    old.ScriptList.ScriptCount = len(old.ScriptList.ScriptRecord)
    # Feature records must be alphabetical; fix every LangSys index afterward.
    indexed = sorted(enumerate(old.FeatureList.FeatureRecord), key=lambda pair: pair[1].FeatureTag)
    remap = {before: after for after, (before, _) in enumerate(indexed)}
    old.FeatureList.FeatureRecord = [record for _, record in indexed]
    for script in old.ScriptList.ScriptRecord:
        for lang in [script.Script.DefaultLangSys] + [r.LangSys for r in script.Script.LangSysRecord]:
            if lang:
                lang.FeatureIndex = sorted(remap[i] for i in lang.FeatureIndex)
                if lang.ReqFeatureIndex != 65535:
                    lang.ReqFeatureIndex = remap[lang.ReqFeatureIndex]


def extend(font):
    cmap = font.getBestCmap()
    upem = font['head'].unitsPerEm
    gap = round(upem * .045)
    slope = math.tan(math.radians(-font['post'].italicAngle))
    added = {}
    # Below marks reuse the exact weight-specific upstream accent shape.
    for cp, source in [(0x323, 'dotaccent'), (0x32E, 'breve'), (0x331, 'macron'), (0x32D, 'circumflex')]:
        x0, y0, x1, y1 = bounds(font, source)
        dy = -gap - y1
        dx = round(-(x0 + x1) / 2 + slope * dy)
        name = f'uni{cp:04X}'
        install(font, name, component(font, [(source, (1, 0, 0, 1, dx, dy))]), 0, cp)
        added[cp] = name
    # Build every Latin canonical composite whose components are available.
    # Iteration admits stacked combinations, e.g. r + dot below + macron.
    inherited = {}
    targets = 'ḥṣṭḫṃḍṛṇṯḇḏḵḡḷṝḹṉṟṅṁḳḻḗṓṗẓ'
    for _ in range(3):
        cmap = font.getBestCmap()
        for cp in sorted({ord(ch) for ch in targets + targets.upper()}):
            if cp in cmap or 'LATIN' not in ud.name(chr(cp), ''):
                continue
            parts = ud.decomposition(chr(cp)).split()
            if len(parts) != 2 or any(p.startswith('<') for p in parts):
                continue
            base_cp, mark_cp = map(lambda p: int(p, 16), parts)
            if base_cp not in cmap or mark_cp not in cmap or not ud.combining(chr(mark_cp)):
                continue
            base, mark = cmap[base_cp], cmap[mark_cp]
            bx0, by0, bx1, by1 = bounds(font, base)
            mx0, my0, mx1, my1 = bounds(font, mark)
            below = ud.combining(chr(mark_cp)) in {202, 220}
            dy = by0 - gap - my1 if below else by1 + gap - my0
            dx = round((bx0 + bx1 - mx0 - mx1) / 2 + slope * dy)
            name = f'uni{cp:04X}'
            install(font, name, component(font, [(base, (1, 0, 0, 1, 0, 0)), (mark, (1, 0, 0, 1, dx, dy))]), font['hmtx'][base][0], cp)
            added[cp] = name
            inherited[name] = base
    # Half-ring letters: open circular strokes, not punctuation substitutions.
    xheight = font['OS/2'].sxHeight
    weight = font['OS/2'].usWeightClass
    radius = upem * .105
    stroke = upem * (.025 + (weight - 400) / 300 * .018)
    cy = xheight * .94
    for cp, side in [(0x2BE, 1), (0x2BF, -1)]:
        pen = TTGlyphPen(None)
        curve = TransformPen(Cu2QuPen(pen, max_err=1), (side, 0, slope, 1, radius + stroke, cy))
        k = .5522847498
        r, inner = radius, radius-stroke
        curve.moveTo((0, -r))
        curve.curveTo((k*r, -r), (r, -k*r), (r, 0))
        curve.curveTo((r, k*r), (k*r, r), (0, r))
        curve.lineTo((0, inner))
        curve.curveTo((k*inner, inner), (inner, k*inner), (inner, 0))
        curve.curveTo((inner, -k*inner), (k*inner, -inner), (0, -inner))
        curve.closePath()
        name = f'uni{cp:04X}'
        install(font, name, pen.glyph(), round(radius*2 + stroke*2), cp)
        added[cp] = name
    # Schwa is a rotated e; eng already exists upstream. Other IPA awaits drawing.
    for cp, source in [(0x259, 'e'), (0x18F, 'e')]:
        x0, y0, x1, y1 = bounds(font, source)
        name = f'uni{cp:04X}'
        scale = font['OS/2'].sCapHeight / (y1-y0) if cp == 0x18F else 1
        install(font, name, component(font, [(source, (-scale, 0, 0, -scale, round((x0+x1)*scale), round((y0+y1)*scale)))]), round(font['hmtx'][source][0]*scale), cp)
        added[cp] = name
    # Attach our below marks even when no precomposed Unicode letter exists.
    below_marks = [f'uni{cp:04X}' for cp in (0x323, 0x32E, 0x331, 0x32D)]
    fea = ['languagesystem DFLT dflt;', 'languagesystem latn dflt;']
    for name in below_marks:
        fea.append(f'markClass {name} <anchor 0 0> @BELOW;')
    fea.append('feature mark {')
    cmap = font.getBestCmap()
    bases = sorted({name for cp, name in cmap.items() if 'LATIN' in ud.name(chr(cp), '') and ud.category(chr(cp)).startswith('L')})
    for base in bases:
        x0, y0, x1, y1 = bounds(font, base)
        fea.append(f'pos base {base} <anchor {round((x0+x1)/2 + slope*y0)} {y0}> mark @BELOW;')
    fea.append('} mark;')
    merge_mark_layout(font, '\n'.join(fea))
    classes = font['GDEF'].table.GlyphClassDef.classDefs
    classes.update({name: 3 for name in below_marks})
    classes.update({name: 1 for cp, name in added.items() if cp not in (0x323, 0x32E, 0x331, 0x32D)})
    # Extend class-based kerning membership to the new composites.
    for lookup in font['GPOS'].table.LookupList.Lookup:
        for sub in lookup.SubTable:
            sub = getattr(sub, 'ExtSubTable', sub)
            for attr in ('ClassDef1', 'ClassDef2'):
                classes = getattr(sub, attr, None)
                if classes:
                    for name, base in inherited.items():
                        if base in classes.classDefs:
                            classes.classDefs[name] = classes.classDefs[base]
                        if attr == 'ClassDef1' and base in sub.Coverage.glyphs and name not in sub.Coverage.glyphs:
                            sub.Coverage.glyphs.append(name)
                    if attr == 'ClassDef1':
                        sub.Coverage.glyphs.sort(key=font.getGlyphID)
    font['OS/2'].recalcUnicodeRanges(font)
    font['OS/2'].usLastCharIndex = min(max(cmap), 65535)
    return added


def rename(font, style):
    postscript = FAMILY.replace(' ', '') + '-' + style.replace(' ', '')
    values = {0: font['name'].getDebugName(0) + '; scholarly additions Copyright 2026 Wheel of Heaven contributors',
              1: FAMILY, 2: style, 3: '0.1.0;' + postscript, 4: FAMILY+' '+style,
              5: 'Version 0.100; scholarly pilot', 6: postscript, 16: FAMILY, 17: style}
    font['name'].names = [r for r in font['name'].names if r.nameID not in values and r.nameID < 256]
    for name_id, value in values.items():
        for platform, encoding, language in [(3, 1, 0x409), (1, 0, 0)]:
            font['name'].setName(value, name_id, platform, encoding, language)
    font['head'].fontRevision = .1
    if 'STAT' in font:
        del font['STAT']
    if 'DSIG' in font:
        del font['DSIG']


def main():
    manifest = json.loads((ROOT/'upstream/manifest.json').read_text())
    for name, digest in manifest['sha256'].items():
        assert hashlib.sha256((ROOT/'upstream'/name).read_bytes()).hexdigest() == digest, name
    report = {}
    for italic in (False, True):
        source = ROOT/'upstream'/('Jost-Italic.ttf' if italic else 'Jost-Roman.ttf')
        for weight in (400, 700):
            font = instantiateVariableFont(TTFont(source, recalcTimestamp=False), {'wght': weight}, inplace=True, updateFontNames=True)
            font.recalcTimestamp = False
            style = ('Bold Italic' if italic else 'Bold') if weight == 700 else ('Italic' if italic else 'Regular')
            # Unmodified coverage-restoration artifacts are separate from the fork.
            font.flavor = 'woff2'
            font.save(ROOT/'fonts'/f'Jost-{style.replace(" ", "")}.woff2')
            font.flavor = None
            added = extend(font)
            rename(font, style)
            stem = 'FirmamentSans-' + style.replace(' ', '')
            font.save(ROOT/'fonts'/f'{stem}.ttf')
            font.flavor = 'woff2'
            font.save(ROOT/'fonts'/f'{stem}.woff2')
            report[style] = {'added': {f'U+{cp:04X}': chr(cp) for cp in sorted(added)}, 'total_codepoints': len(font.getBestCmap())}
            print(style, len(added), 'added characters')
    (ROOT/'audit/build.json').write_text(json.dumps(report, indent=2, ensure_ascii=False)+'\n')
    specimen = ROOT/'specimen/index.html'
    html = specimen.read_text()
    for path in (ROOT/'fonts').glob('*.woff2'):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        html = re.sub(re.escape('../fonts/' + path.name) + r'(?:\?v=[a-f0-9]+)?', '../fonts/' + path.name + '?v=' + digest, html)
    specimen.write_text(html)


if __name__ == '__main__':
    main()
