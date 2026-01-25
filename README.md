MKV Subtitle Extractor – Jellyfin-Aware Naming

Overview:

The MKV Subtitle Extractor is a Python tool for extracting subtitles from .mkv files while preserving metadata in a Jellyfin-compatible way. Many MKVs contain multiple subtitle tracks with overlapping languages, flags, or properties. This tool handles text (.srt, .ass, .ssa) and image (.sub/.idx, .sup) tracks and generates clear filenames reflecting language, default/forced flags, and hearing-impaired indicators. Ideal for libraries with container subtitles, manually collected subtitles (.External), and OpenSubtitles downloads. Consistent naming and custom tags allow coexistence without overwriting.

Design Philosophy:

The tool aims for clarity, reproducibility, and Jellyfin compatibility. Each track gets a unique, deterministic filename based on its metadata and track ID. The .Extracted tag marks container-extracted tracks. External or OpenSubtitles tracks use .External or .OpenSubtitles. Counters are appended to .Extracted when tracks cannot be distinguished by language, flags, or type (common in pt/pt-br, Spanish accents, Chinese variants). This ensures reproducible, human-readable filenames.


Naming Convention & Filename structure:

(basename)[.default][.(lang)][.(hi)][.forced].Extracted[(counter)].(ext)

Components:
- (basename): Video filename without .mkv
- .default: Track is flagged as default
- .(lang): Normalized language code from mapping.txt
- .(hi): Hearing-impaired / SDH / CC
- .forced: Forced subtitle track
- .Extracted: Container-extracted tag
- [(counter)]: Optional counter for indistinguishable tracks
- (ext): File extension based on codec (.srt, .ass, .sub/.idx, .sup)

Key Notes:
- .Extracted improves Jellyfin UI readability over numeric-only counters.
- Counters appear only for tracks that cannot be distinguished by Jellyfin.
- Supports multiple sources simultaneously: Extracted, External, OpenSubtitles.
- Prevents overwriting of previously collected subtitles.

Parsing & Workflow:
1. Track Analysis:
   - mkvmerge -J extracts JSON metadata.
   - Captures per-track info: ID, language, name, codec, default/forced flags.
   - Detects HI/SDH using regex on track names.
   - Determines track type: text or image.
2. Language Mapping & Normalization:
   - Uses mapping.txt to normalize language codes.
   - Undefined or "und" codes marked as None.
3. Filename Assignment & Collision Handling:
   - Generates filenames per convention.
   - Checks duplicates; adds counter as needed.
   - Default tracks prioritized in collisions.
   - Image tracks produce .sub/.idx pairs, text tracks .srt/.ass.
4. Simulation / Extraction:
   - Simulation: Prints filenames for review.
   - Extraction: mkvextract writes files to disk.
5. Post-run reporting:
   - Tracks with missing language codes.
   - Tracks with 3-letter codes.
   - Summary of text vs. image tracks.

Workflow Diagram (ASCII):

MKV Container
 └─ Track Extraction (mkvmerge -J)
     └─ Metadata Collection (language, name, codec, flags, HI/SDH)
          |
          v
 Language Mapping & Normalization (mapping.txt)
          |
          v
 Filename Assignment ((basename)[.default][.(lang)][.(hi)][.forced].Extracted[(counter)].(ext))
          |
          v
 Output
  ├─ Simulation → print filenames
  └─ Extraction → save subtitle files

Counter Logic:
- Applied when multiple tracks share the same (lang), flags, or codec.
- Common in pt/pt-br, Spanish with accents, Chinese variants.
- Deterministic based on track ID.
- Ensures uniqueness in Jellyfin even when sublanguage distinctions cannot be parsed.

Usage:
1. Install MKVToolNix and Python 3; ensure both are in system PATH.
2. Create a project folder.
3. Add mapping.txt (language normalization) and paths.txt (one folder per line, recursive).
4. Run: python mkv_subtitle_extractor.py
5. Select subtitle filter: All / Text / Image
6. Select mode: Simulate / Extract
7. Review simulation output before extraction.

Example Filenames (some combinations):

Text Tracks:
- Movie.default.en.Extracted.srt            → Default English
- Movie.en.Extracted.srt                     → English
- Movie.en.sdh.Extracted.srt                 → English, HI/SDH
- Movie.en.forced.Extracted.srt              → English, Forced
- Movie.default.en.sdh.Extracted.srt         → Default, English, HI/SDH
- Movie.default.en.forced.Extracted.srt      → Default, English, Forced
- Movie.pt.Extracted.srt                     → Portuguese
- Movie.pt.Extracted1.srt                    → Duplicate Portuguese
- Movie.es.Extracted.srt                     → Spanish
- Movie.es.Extracted1.srt                    → Duplicate Spanish

Image Tracks:
- Movie.en.Extracted.sub/.idx                → English VOBSUB
- Movie.pt.Extracted.sub/.idx                → Portuguese VOBSUB
- Movie.en.sdh.Extracted.sup                 → English PGS, HI/SDH
- Movie.default.en.forced.Extracted.sup      → Default + Forced English PGS

License:
MIT
