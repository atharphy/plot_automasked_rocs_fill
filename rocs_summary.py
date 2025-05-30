import os
import sys
import argparse
from datetime import datetime
from collections import defaultdict
import subprocess
import re

AUTOMASKED_DIR = "/nfspixelraid/nfspixelraid/users/masks/automasked_channels"
TEMP_INPUT_FILE = "input.dat"
EXPANDED_INPUT_FILE = "input_expanded.dat"
ROCS_PY_SCRIPT = "rocs_frequency.py"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_filename_time(filename):
    try:
        parts = filename.split("_")
        datetime_part = parts[1] + "_" + parts[2]
        return datetime.strptime(datetime_part, "%Y-%m-%d_%H:%M:%S")
    except:
        return None

def get_files(start_time, end_time):
    matched_files = []
    for fname in os.listdir(AUTOMASKED_DIR):
        if not fname.startswith("automasked_") or not fname.endswith(".txt"):
            continue
        ftime = parse_filename_time(fname)
        if ftime and start_time <= ftime <= end_time:
            matched_files.append(os.path.join(AUTOMASKED_DIR, fname))
    return sorted(matched_files)

def classify_layer(roc_name):
    if "BPix" in roc_name:
        if "LYR1" in roc_name:
            return "BPix L1"
        elif "LYR2" in roc_name:
            return "BPix L2"
        elif "LYR3" in roc_name:
            return "BPix L3"
        elif "LYR4" in roc_name:
            return "BPix L4"
    elif "FPix" in roc_name:
        if "D1" in roc_name:
            return "FPix D1"
        elif "D2" in roc_name:
            return "FPix D2"
        elif "D3" in roc_name:
            return "FPix D3"
    return None

def extract_rocs(filepaths, output_file):
    frequency = defaultdict(int)
    all_lines = []
    blacklisted_rocs = set()
    all_rocs = set()
    range_pattern = re.compile(r'->\s*(\S+)_ROC\[(\d+):(\d+)\]')
    full_pattern = re.compile(r'(FPix|BPix)_\S+_ROC\d+')

    for path in filepaths:
        stop_parsing = False
        with open(path, "r") as f:
            for line in f:
                if stop_parsing:
                    continue
                if line.startswith("*****") and "SUMMARY" in line:
                    stop_parsing = True
                    continue
                if not line or line.startswith("---") or line.startswith("*") or line.startswith("#"):
                    continue
                is_blacklisted = "- BLACKLISTED" in line
                match = range_pattern.search(line)
                if match:
                    base = match.group(1)
                    start = int(match.group(2))
                    end = int(match.group(3))
                    for i in range(start, end + 1):
                        roc = f"{base}_ROC{i}"
                        frequency[roc] += 1
                        all_rocs.add((roc, is_blacklisted))
                else:
                    match_full = full_pattern.search(line)
                    if match_full:
                        roc = match_full.group(0)
                        frequency[roc] += 1
                        all_rocs.add((roc, is_blacklisted))

    with open(output_file, "w") as out:
        for roc, is_blacklisted in sorted(all_rocs):
            count = frequency[roc]
            if is_blacklisted:
                out.write(f"Badrocs: {roc} {count} blacklisted\n")
            else:
                out.write(f"Badrocs: {roc} {count}\n")

def parse_summary(file):
    summary = defaultdict(lambda: {"masked_rocs": 0, "blacklisted": 0})
    known_totals = {
        'BPix L1': 1536,
        'BPix L2': 3584,
        'BPix L3': 5632,
        'BPix L4': 8192,
        'FPix D1': 3584,
        'FPix D2': 3584,
        'FPix D3': 3584,
    }
    with open(file) as f:
        for line in f:
            line = line.strip()
            if not line.startswith("Badrocs:"):
                continue
            parts = line.split()
            roc = parts[1]
            is_blacklisted = "blacklisted" in line
            layer = classify_layer(roc)
            if layer:
                summary[layer]["masked_rocs"] += 1
                if is_blacklisted:
                    summary[layer]["blacklisted"] += 1
    print("\n" + "=" * 80)
    print(f"{'SUMMARY':^80}")
    print("=" * 80)
    print(f"{'Layer':<10} {'Masked':>8} {'Total':>8} {'% Automasked':>15} {'Blacklisted':>14} {'% Blacklisted':>15}")
    print("-" * 80)
    totals = {"masked_rocs": 0, "blacklisted": 0, "total_rocs": 0}
    for layer, total_rocs in known_totals.items():
        masked = summary[layer]["masked_rocs"]
        black = summary[layer]["blacklisted"]
        auto_pct = 100 * masked / total_rocs
        black_pct = 100 * black / total_rocs
        print(f"{layer:<10} {masked:8} {total_rocs:8} {auto_pct:14.2f}% {black:14} {black_pct:14.2f}%")
        totals["masked_rocs"] += masked
        totals["blacklisted"] += black
        totals["total_rocs"] += total_rocs
    total_auto = 100 * totals["masked_rocs"] / totals["total_rocs"]
    total_black = 100 * totals["blacklisted"] / totals["total_rocs"]
    print("-" * 80)
    print(f"{'Total':<10} {totals['masked_rocs']:8} {totals['total_rocs']:8} {total_auto:14.2f}% "
          f"{totals['blacklisted']:14} {total_black:14.2f}%")

def filter_input(input_file, output_file, blacklisted_only):
    with open(input_file) as fin, open(output_file, "w") as fout:
        for line in fin:
            if blacklisted_only:
                if "blacklisted" in line:
                    fout.write(line.replace(" blacklisted", ""))
            else:
                fout.write(line.replace(" blacklisted", ""))

def run_rocs_frequency(input_file, output_dir):
    cmd = ["python", os.path.join(SCRIPT_DIR, ROCS_PY_SCRIPT), input_file, "--output-dir", output_dir]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="Start time (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--end", required=True, help="End time (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--fill", required=True, help="Fill number")
    parser.add_argument("-blacklisted", action="store_true", help="Use only blacklisted ROCs")
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")
    matched_files = get_files(start_dt, end_dt)

    if not matched_files:
        print("No files found in range.")
        return

    expanded_file = os.path.join(SCRIPT_DIR, EXPANDED_INPUT_FILE)
    extract_rocs(matched_files, expanded_file)
    parse_summary(expanded_file)

    filtered_file = os.path.join(SCRIPT_DIR, TEMP_INPUT_FILE)
    filter_input(expanded_file, filtered_file, args.blacklisted)

    output_dir = os.path.join(SCRIPT_DIR, f"fill_{args.fill}")
    if args.blacklisted:
        output_dir = os.path.join(output_dir, "blacklisted")
    os.makedirs(output_dir, exist_ok=True)

    run_rocs_frequency(filtered_file, output_dir)

if __name__ == "__main__":
    main()