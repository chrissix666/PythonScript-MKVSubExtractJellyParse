
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MKV Subtitle Extractor / Simulator
Enhanced version: robust counter handling for Default and Forced tracks,
with correct simulate/extract behavior.
"""

import os, sys, json, subprocess, re

# ==========================
# CONFIGURATION
# ==========================
MKVMERGE = "mkvmerge"
MKVEXTRACT = "mkvextract"

class color:
    WHITE  = "\033[97m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    PINK   = "\033[95m"
    RESET  = "\033[0m"

TEXT_SUB_CODECS = {"S_TEXT/UTF8", "S_TEXT/ASS", "S_TEXT/SSA"}

# ==========================
# POST-RUN REPORT COLLECTION
# ==========================
LANG_NONE_TRACKS = []
LANG_3CHAR_TRACKS = []

# ==========================
# HELPER FUNCTIONS
# ==========================
def load_mapping(mapping_file="mapping.txt"):
    mapping = {}
    try:
        with open(mapping_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "#" in line:
                    line = line.split("#",1)[0].strip()
                if "=" not in line:
                    continue
                src, tgt = line.split("=",1)
                mapping[src.strip().lower()] = tgt.strip().lower()
    except FileNotFoundError:
        print(f"❌ Mapping file '{mapping_file}' not found!")
        sys.exit(1)
    return mapping

def read_paths(paths_file="paths.txt"):
    paths_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), paths_file)
    if not os.path.exists(paths_file):
        print("❌ paths.txt missing!")
        sys.exit(1)
    with open(paths_file, encoding="utf-8") as f:
        folders = [l.strip() for l in f if l.strip()]
    if not folders:
        print("❌ paths.txt is empty!")
        sys.exit(1)
    return folders

def build_sub_filename(base_name, lang=None, hi=None, forced=False, default=False, counter=None, ext=".srt"):
    parts = [base_name]
    if default:
        parts.append("default")
    if lang:
        parts.append(lang)
    if hi:
        parts.append(hi)
    if forced:
        parts.append("forced")
    parts.append("Extracted")
    if counter:
        parts[-1] += str(counter)
    filename = ".".join(parts) + ext
    return filename

# ==========================
# SUBTITLE ANALYSIS
# ==========================
def analyze_subs(mkv_path, lang_mapping, subtitle_filter):
    base_name = os.path.splitext(os.path.basename(mkv_path))[0]
    print(f"{color.WHITE}{mkv_path}{color.RESET}")
    try:
        r = subprocess.run([MKVMERGE, "-J", mkv_path], capture_output=True, text=True)
        info = json.loads(r.stdout)
    except Exception as e:
        print("❌ Error reading mkvmerge JSON:", e)
        return []

    tracks = []
    for t in sorted(info.get("tracks", []), key=lambda x: x.get("id",0)):
        if t.get("type") != "subtitles":
            continue
        props = t.get("properties", {})
        codec = props.get("codec_id")
        tid = t.get("id")
        name = props.get("track_name","")
        forced_flag = props.get("forced_track", False) or bool(re.search(r"forced|only|foreign", name, re.I))
        default_flag = props.get("default_track", False)

        # ====== LANGUAGE LOGIC ======
        lang_code = (props.get("language") or "").strip().lower()
        lang = lang_mapping.get(lang_code, lang_code) if lang_code else None

        if not lang or lang=="und":
            lang = None

        # ====== REPORT COLLECTION ======
        if lang is None:
            LANG_NONE_TRACKS.append({
                "file": mkv_path,
                "track_id": tid,
                "codec": codec,
                "name": name
            })
        elif isinstance(lang, str) and len(lang) == 3:
            LANG_3CHAR_TRACKS.append({
                "file": mkv_path,
                "track_id": tid,
                "lang": lang,
                "codec": codec,
                "name": name
            })

        hi_flag = None
        if re.search(r"hi|sdh|cc", name, re.I):
            hi_flag = re.search(r"hi|sdh|cc", name, re.I).group(0).lower()

        typ = "text" if codec in TEXT_SUB_CODECS else ("image" if codec=="S_VOBSUB" else "image")
        exts = [".srt"] if typ=="text" else [".sub",".idx"] if codec=="S_VOBSUB" else [".sup"]

        if subtitle_filter=="text" and typ!="text":
            continue
        if subtitle_filter=="bild" and typ!="image":
            continue

        tracks.append({
            "id": tid,
            "type": typ,
            "codec": codec,
            "forced": forced_flag,
            "default": default_flag,
            "lang": lang,
            "hi": hi_flag,
            "exts": exts
        })
    return tracks

# ==========================
# NAME ASSIGNMENT WITH COLLISION HANDLING
# ==========================
def assign_filenames(base_name, tracks):
    used_names = {}
    for track in tracks:
        track["assigned_names"] = []
        for ext in track["exts"]:
            counter = None
            default_flag = track["default"]
            candidate = build_sub_filename(
                base_name, track["lang"], track["hi"],
                track["forced"], default_flag, counter, ext
            )
            while candidate in used_names:
                if default_flag:
                    if not used_names[candidate]["default"]:
                        counter = 1
                    else:
                        counter = used_names[candidate]["counter"]+1 if "counter" in used_names[candidate] else 1
                else:
                    counter = used_names[candidate]["counter"]+1 if "counter" in used_names[candidate] else 1
                candidate = build_sub_filename(
                    base_name, track["lang"], track["hi"],
                    track["forced"], default_flag, counter, ext
                )
            track["assigned_names"].append(candidate)
            used_names[candidate] = {
                "default": default_flag,
                "counter": counter if counter else 0
            }
    return tracks

# ==========================
# SIMULATION / EXTRACTION
# ==========================
def process_mkv(mkv_path, lang_mapping, subtitle_filter, mode):
    tracks = analyze_subs(mkv_path, lang_mapping, subtitle_filter)
    tracks = assign_filenames(os.path.splitext(os.path.basename(mkv_path))[0], tracks)

    text_count = 0
    image_count = 0

    for track in tracks:
        for fname in track["assigned_names"]:
            if track["type"]=="text":
                text_count += 1
                print(f"{color.YELLOW}[{track['id']}] TEXT: {track['lang']} -> {fname}{color.RESET}")
            else:
                image_count += 1
                print(f"{color.BLUE}[{track['id']}] IMAGE: {track['lang']} -> {fname}{color.RESET}")

            if mode=="extract":
                out_dir = os.path.dirname(mkv_path)
                out_path = os.path.join(out_dir, fname)
                try:
                    subprocess.run(
                        [MKVEXTRACT, "tracks", mkv_path, f"{track['id']}:{out_path}"],
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    print(f"❌ Extraction error: {e}")

    print(f"  Stats: total={len(tracks)}, text={text_count}, image={image_count}")
    print("-"*50)

# ==========================
# MAIN
# ==========================
def main():
    lang_mapping = load_mapping("mapping.txt")

    print("Select subtitle filter:")
    print("  1) all")
    print("  2) text")
    print("  3) bild")
    subtitle_filter = {"1":"all","2":"text","3":"bild"}.get(input("Choice [1-3]: ").strip())
    if not subtitle_filter:
        sys.exit("❌ Invalid choice!")

    print("Select mode:")
    print("  1) simulate")
    print("  2) extract")
    mode = {"1":"simulate","2":"extract"}.get(input("Choice [1-2]: ").strip())
    if not mode:
        sys.exit("❌ Invalid choice!")

    for folder in read_paths():
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(".mkv"):
                    process_mkv(os.path.join(root, file), lang_mapping, subtitle_filter, mode)

    # ==========================
    # POST-RUN REPORT
    # ==========================
    print("\n" + "="*60)
    print("POST-RUN LANGUAGE REPORT")
    print("="*60)

    print("\n[1] Tracks with missing language (lang = None)")
    if not LANG_NONE_TRACKS:
        print("  everything fine")
    else:
        for t in LANG_NONE_TRACKS:
            print(f"  {t['file']} | track {t['track_id']} | {t['codec']} | {t['name']}")

    print("\n[2] Tracks with 3-letter language codes")
    if not LANG_3CHAR_TRACKS:
        print("  everything fine")
    else:
        for t in LANG_3CHAR_TRACKS:
            print(f"  {t['file']} | track {t['track_id']} | {t['lang']} | {t['codec']} | {t['name']}")

    print("="*60)

# ==========================
# ENTRY POINT
# ==========================
if __name__=="__main__":
    try:
        subprocess.run([MKVMERGE,"--version"], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([MKVEXTRACT,"--version"], check=True, stdout=subprocess.DEVNULL)
    except Exception:
        sys.exit("❌ mkvmerge or mkvextract not found!")

    main()
