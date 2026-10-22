# Firmament Sans

**Yesterday’s clarity. Tomorrow’s possibilities.**

A scholarly extension of **Jost**, the geometric sans-serif designed by **Owen Earl / indestructible type**.
The spirit of 1920s German design, extended for the knowledge we pass forward.

[Explore the typeface](https://firmament.wheelofheaven.world/) · [Download the family](https://firmament.wheelofheaven.world/downloads/FirmamentSans-0.1.zip) · [Design story](https://firmament.wheelofheaven.world/#story) · [Script study](https://github.com/wheelofheaven/firmament.wheelofheaven.world/blob/main/docs/script-expansion.md)

**Status: 0.1 optical-review pilot.** Four static styles: Regular, Italic, Bold, and Bold Italic, in TTF and WOFF2.
584 Unicode mappings per style, including 60 scholarly additions to full Jost.
The [dedicated showcase](https://firmament.wheelofheaven.world/) uses Firmament; adoption on the main Wheel of Heaven website is managed separately.

## Form follows function

Jost brings the spirit of Futura into contemporary use; Firmament carries that approach into scholarly reading.
Our wider outlook draws on three distinct currents of 1920s Germany: the Bauhaus’s practical design experiments, the New Typography’s organisation of information, and New Objectivity’s close attention to its subject.
The [public design story](https://firmament.wheelofheaven.world/#story) links the historical sources and distinguishes them from our contemporary interpretation.

We imagine a future in which knowledge is easier to share, study, and question.
For us, the best way to pass it from one generation to the next begins with form following function: readable letters, visible distinctions, and tools that others can inspect and improve.
A macron and a dot below a consonant each have a job to do.
Their place in the typeface follows from that purpose.

Firmament began with the essays and etymologies of [Wheel of Heaven](https://www.wheelofheaven.world/).
Our feet stay on the baseline; our eyes stay on the stars.

## What the pilot adds

60 mapped codepoints per style, bringing coverage from 524 to 584:

- Scholarly letters including `ḥ ṣ ṭ ḫ ṃ ḍ ṛ ṇ ṯ ḇ ḏ ḵ ḡ ḷ ṝ ḹ`, with uppercase partners.
- Half-ring letters `ʾ ʿ`, drawn as circular strokes rather than substituted punctuation.
- Schwa `ə Ə`, derived from Jost’s curved e construction.
- Combining dot below, breve below, line below, and circumflex below, with Latin base-attachment positioning.

The accent components inherit Jost’s weight-specific outlines.
Existing Latin and Cyrillic outlines and layout are retained.
Precomposed additions and their canonical decompositions are checked with HarfBuzz.
The first build is deliberately static; it does not extend the upstream variable fonts.

## Try it

The [live one-page specimen](https://firmament.wheelofheaven.world/) includes an editable typesetter, a searchable character inventory, four-style proofs, multilingual reading samples, and licensed downloads.
Its Zola source lives in [firmament.wheelofheaven.world](https://github.com/wheelofheaven/firmament.wheelofheaven.world).

Download the four `FirmamentSans-*.ttf` or `FirmamentSans-*.woff2` files from [scholar/fonts](scholar/fonts).
The files named `Jost-*` in the same directory are full-coverage upstream comparison builds, not renamed derivatives.

```sh
mise run setup
mise run build
mise run check
mise run preview
```

Open <http://127.0.0.1:18289/specimen/> for side-by-side old subset, full Jost, and Firmament Sans samples, four-style proofs, a size slider, and light/dark backgrounds.
Python 3.13 and pinned dependencies are used; equivalent direct commands are in `mise.toml`.
CI rebuilds the checked-in artifacts and runs shaping checks.

## Corpus audit

[The report](scholar/audit/README.md) inventories published Markdown source and library JSON values across all ten site locales.
It excludes draft Markdown and library review, curation, and audio directories.
It does not claim to measure rendered fallback: quotations, source scripts, and headings can use other families.

Of 162 distinct Latin/modifier/combining characters absent from the old regular site font:

| Stage | Gaps addressed | Remaining |
|---|---:|---:|
| Full upstream Jost | 47 | 115 |
| Firmament Sans pilot | 37 additional observed characters | 78 |

The 60 new codepoints include uppercase counterparts and support marks not present in the corpus.
[coverage.json](scholar/audit/coverage.json) records counts, Unicode names, normalization forms, and example paths.
[remaining.json](scholar/audit/remaining.json) is the next design backlog.
Counts include all locales and library strings; they must not be read as English body-text counts.
Refresh with `mise run audit` when the website is checked out alongside this repository.

## Design review still needed

- Optical spacing and accent placement across browsers and reading sizes, especially stacked marks and italic forms.
- Remaining IPA, modifier letters, Egyptological alef, and additional Latin orthographies (including Vietnamese).
- General mark-to-mark stacking and arbitrary above-mark placement; the current attachment addition covers the four below marks.
- Broader kerning review for new letters; existing upstream sample shaping is regression-checked.
- Variable-font masters and interpolation if a full variable release is desired.

No glyphs have been borrowed from an unrelated typeface.

## Beyond Latin and Cyrillic

The proposed direction is a coordinated family that respects how each script is read.
These are evaluation priorities, not features included in 0.1:

| Script | Proposed route |
| --- | --- |
| Greek | First original extension, including polytonic accents and native-reader review |
| Hebrew | Dedicated companion, with vowel points, cantillation, and mixed-direction proofs |
| Arabic | Specialist-led companion, with contextual joining and mark positioning |
| Cuneiform | Established scholarly companion before considering a bespoke sign design |
| CJK | Regional Chinese, Japanese, and Korean companions; evaluate Source Han Sans / Noto Sans CJK |

Use reviewed existing companions to provide reliable coverage while original designs develop.
Read the [full feasibility study](https://github.com/wheelofheaven/firmament.wheelofheaven.world/blob/main/docs/script-expansion.md) for corpus evidence, candidate families, relative effort, and release gates.
Form should follow the function of each script, language, and reader.

## Source and provenance

This repository preserves Jost’s history, sources, and original font artifacts.
The original project README is [README.upstream.md](README.upstream.md).
New work is isolated under `scholar/`:

- `upstream/`: pinned Google Fonts Roman/Italic variable inputs and checksums, plus the old website subset for comparison.
- `scripts/build.py`: the canonical, reproducible component/curve construction for the pilot.
- `scripts/check.py`: name/style/coverage/shaping/WOFF2 checks and remaining-coverage report.
- `scripts/audit.py`: corpus inventory.
- `specimen/`: browser specimen.

Jost source commit: `35f141c970538f1ed0f235789c19156b3ce2a762`.
Google Fonts input commit: `6e4b84c976cadb3c49a40fd9a1c203e4f7fcf2da`.
The Google Fonts build is used because it is the full-coverage distribution underlying the website’s font family; the original repository’s older build script is preserved for reference.
The extension is a scripted build layer over those pinned inputs, not an edit to the historical UFO masters.

## License and credits

[SIL Open Font License 1.1](OFL.txt).
Retain the original copyright and license when redistributing fonts.
Jost: Owen Earl and the Jost Project Authors.
Scholarly additions: Wheel of Heaven contributors, 2026.
Firmament Sans is an independent derivative; no upstream endorsement is implied.
