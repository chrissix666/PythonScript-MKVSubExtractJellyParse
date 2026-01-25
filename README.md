MKV Subtitle Extractor – Jellyfin-Aware Naming

Overview:
The MKV Subtitle Extractor is a Python tool designed to extract subtitles from .mkv files while preserving all metadata in a way that Jellyfin can reliably parse. Many MKV containers contain multiple subtitle tracks that share the same language, flags, or other characteristics, which can confuse standard extraction tools. This extractor handles both text-based (.srt, .ass, .ssa) and image-based (.sub/.idx, .sup) subtitles and generates human- and Jellyfin-friendly filenames reflecting language, default/forced flags, and hearing-impaired indicators. It is intended for libraries with multiple subtitle sources, including container-embedded subtitles, manually collected subtitles (.External), and automatically downloaded subtitles (OpenSubtitles plugin). By using consistent naming and custom tags, all tracks can coexist without overwriting or confusing Jellyfin.

Design Philosophy:
The primary goals are clarity, reproducibility, and Jellyfin compatibility. Each track is assigned a unique filename based on track metadata and ID. The .Extracted tag identifies container-extracted tracks. External or OpenSubtitles tracks use .External or .OpenSubtitles, allowing multiple sources to coexist in the same folder. Counters are appended to .Extracted when tracks cannot be distinguished by Jellyfin due to duplicate languages, multiple Spanish accents, Portuguese variants (pt/pt-br), or Chinese variants (zh-Hans/zh-Hant). This ensures deterministic, reproducible, and human-readable filenames.

Naming Convention:
Filenames follow this structure:

<basename>[.default][.<lang>][.<hi>][.forced].Extracted[<counter>].<ext>

Components:
- <basename>: Video filename without .mkv
- .default: Track is flagged as default
- .<lang>: Normalized language code from mapping.txt
- .<hi>: Hearing-impaired / SDH / CC
- .forced: Forced subtitle track
- .Extracted: Custom tag indicating container extraction
- [<counter>]: Optional numeric counter for indistinguishable duplicates
- <ext>: File extension based on codec (.srt, .ass, .sub/.idx, .sup)

Key Notes:
- .Extracted improves Jellyfin UI readability over raw counters.
- Counters only appear for tracks indistinguishable by language, flags, or type.
- Multiple sources (Extracted, External, OpenSubtitles) can coexist.
- Prevents overwriting previously collected or downloaded subtitles.

Parsing & Workflow:
1. Track Analysis:
   - Uses `mkvmerge -J` to extract JSON metadata.
   - Collects per-track info: ID, language, name, codec, default/forced flags.
   - Detects HI/SDH using regex on track names.
   - Determines track type: text or image-based.
2. Language Mapping & Normalization:
   - Uses mapping.txt to normalize language codes.
   - Undefined codes or "und" are treated as None.
3. Filename Assignment & Collision Handling:
   - Generates filenames according to naming convention.
   - Checks for duplicates; adds counter as needed.
   - Default tracks are prioritized when resolving collisions.
   - Image tracks may generate two files (.sub + .idx), text tracks (.srt/.ass).
4. Simulation or Extraction:
   - Simulation: prints all generated filenames.
   - Extraction: runs mkvextract to write subtitles to disk.
5. Post-run reporting:
   - Tracks with missing language codes.
   - Tracks with 3-letter codes.
   - Summary of text vs. image subtitles.

Workflow Diagram (ASCII):

MKV Container
 └─> Track Extraction (mkvmerge -J)
      └─> Metadata Collection (language, name, codec, flags, HI/SDH)
           |
           v
 Language Mapping & Normalization (mapping.txt)
           |
           v
 Filename Assignment (<basename>[.default][.<lang>][.<hi>][.forced].Extracted[<counter>].<ext>)
           |
           v
 Output
  ├─ Simulation → print filenames
  └─ Extraction → save subtitle files

Counter Logic:
- Applied when multiple tracks share the same <lang>, flags, or codec.
- Common in pt/pt-br, Spanish with accents, Chinese variants.
- Deterministic based on track ID.
- Ensures uniqueness in Jellyfin even when sublanguage distinctions cannot be parsed.

Usage:
1. Install MKVToolNix and Python 3; ensure both are in system PATH.
2. Create a project folder.
3. Add mapping.txt (for language normalization) and paths.txt (one folder per line, recursive processing).
4. Run: python mkv_subtitle_extractor.py
5. Select subtitle filter: All / Text / Image
6. Select mode: Simulate / Extract
7. Review simulation output before extraction.

Example Filenames (covering all combinations):

Text Tracks:
- Movie.default.en.Extracted.srt            → Default English
- Movie.en.Extracted.srt                     → English
- Movie.en.sdh.Extracted.srt                 → English, HI/SDH
- Movie.en.forced.Extracted.srt              → English, Forced
- Movie.default.en.sdh.Extracted.srt         → Default, English, HI/SDH
- Movie.default.en.forced.Extracted.srt      → Default, English, Forced
- Movie.default.en.sdh.forced.Extracted.srt  → Default, English, HI/SDH, Forced
- Movie.pt.Extracted.srt                     → Portuguese
- Movie.pt.Extracted1.srt                    → Duplicate Portuguese track
- Movie.pt-br.Extracted.srt                  → Brazilian Portuguese
- Movie.es.Extracted.srt                     → Spanish (neutral)
- Movie.es.Extracted1.srt                    → Duplicate Spanish track
- Movie.zh-Hans.Extracted.srt                → Chinese Simplified
- Movie.zh-Hant.Extracted.srt                → Chinese Traditional

Image Tracks:
- Movie.en.Extracted.sub/.idx                → English VOBSUB
- Movie.pt.Extracted.sub/.idx                 → Portuguese VOBSUB
- Movie.en.sdh.Extracted.sup                  → English PGS, HI/SDH
- Movie.default.en.forced.Extracted.sup       → Default + Forced English PGS

External / OpenSubtitles Examples:
- Movie.en.External.srt                       → Manual English subtitle
- Movie.pt.OpenSubtitles.srt                  → OpenSubtitles Portuguese subtitle

License:
MIT
