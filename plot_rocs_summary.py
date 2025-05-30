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

def extract_all_rocs_and_count(filepaths, output_file, blacklisted_only=False):
    frequency = defaultdict(int)
    range_pattern = re.compile(r'->\s*(\S+)_ROC\[(\d+):(\d+)\]')
    unique_rocs = set()

    layer_summary = {
        'BPix L1': {"masked_rocs": 0, "blacklisted": 0},
        'BPix L2': {"masked_rocs": 0, "blacklisted": 0},
        'BPix L3': {"masked_rocs": 0, "blacklisted": 0},
        'BPix L4': {"masked_rocs": 0, "blacklisted": 0},
        'FPix D1': {"masked_rocs": 0, "blacklisted": 0},
        'FPix D2': {"masked_rocs": 0, "blacklisted": 0},
        'FPix D3': {"masked_rocs": 0, "blacklisted": 0},
    }

    def classify_roc(roc_name, is_blacklisted):
        if "BPix" in roc_name:
            if "LYR1" in roc_name:
                layer = "BPix L1"
            elif "LYR2" in roc_name:
                layer = "BPix L2"
            elif "LYR3" in roc_name:
                layer = "BPix L3"
            elif "LYR4" in roc_name:
                layer = "BPix L4"
            else:
                return
        elif "FPix" in roc_name:
            if "D1" in roc_name:
                layer = "FPix D1"
            elif "D2" in roc_name:
                layer = "FPix D2"
            elif "D3" in roc_name:
                layer = "FPix D3"
            else:
                return
        else:
            return

        layer_summary[layer]["masked_rocs"] += 1
        if is_blacklisted:
            layer_summary[layer]["blacklisted"] += 1

    for path in filepaths:
        stop_parsing = False
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if stop_parsing:
                    continue
                if line.startswith("*****") and "SUMMARY" in line:
                    stop_parsing = True
                    continue
                if not line or line.startswith("---") or line.startswith("*") or line.startswith("#"):
                    continue
                if blacklisted_only and "BLACKLISTED" not in line:
                    continue

                is_blacklisted = "BLACKLISTED" in line

                match = range_pattern.search(line)
                if match:
                    base = match.group(1)
                    start = int(match.group(2))
                    end = int(match.group(3))
                    for i in range(start, end + 1):
                        roc = f"{base}_ROC{i}"
                        frequency[roc] += 1
                        if roc not in unique_rocs:
                            unique_rocs.add(roc)
                            classify_roc(roc, is_blacklisted)
                else:
                    match_full = re.search(r'((FPix|BPix)_\S+_ROC\d+)', line)
                    if match_full:
                        roc = match_full.group(1)
                        frequency[roc] += 1
                        if roc not in unique_rocs:
                            unique_rocs.add(roc)
                            classify_roc(roc, is_blacklisted)

    with open(output_file, "w") as out:
        for roc, count in sorted(frequency.items()):
            out.write(f"Badrocs: {roc} {count}\n")

    print_summary(layer_summary)
    return output_file

def print_summary(summary):
    print("\n" + "=" * 80)
    print(f"{'SUMMARY':^80}")
    print("=" * 80)
    print(f"{'Layer':<10} {'Masked':>8} {'Total':>8} {'% Automasked':>15} {'Blacklisted':>14} {'% Blacklisted':>15}")
    print("-" * 80)

    totals = {
        "masked_rocs": 0,
        "blacklisted": 0,
        "total_rocs": 0,
    }

    known_totals = {
        'BPix L1': 1536,
        'BPix L2': 3584,
        'BPix L3': 5632,
        'BPix L4': 8192,
        'FPix D1': 3584,
        'FPix D2': 3584,
        'FPix D3': 3584,
    }

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
    parser.add_argument("-save", action="store_true", help="Save the expanded input file")
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(args.end, "%Y-%m-%d %H:%M:%S")

    print("Searching files between:", start_dt, "and", end_dt)
    matched_files = get_files(start_dt, end_dt)
    print(f"Found {len(matched_files)} files")

    if not matched_files:
        print("No files found in range.")
        return

    base_dir = os.path.join(SCRIPT_DIR, f"fill_{args.fill}")
    if args.blacklisted:
        output_dir = os.path.join(base_dir, "blacklisted")
    else:
        output_dir = base_dir
    os.makedirs(output_dir, exist_ok=True)

    expanded_file = os.path.join(SCRIPT_DIR, EXPANDED_INPUT_FILE)
    extract_all_rocs_and_count(matched_files, expanded_file, args.blacklisted)
    print(f"ROC frequency list written to: {expanded_file}")

    if args.save:
        saved_name = os.path.join(output_dir, f"fill_{args.fill}.dat")
        os.rename(expanded_file, saved_name)
        expanded_file = saved_name
        print(f"Saved expanded ROC list to: {expanded_file}")

    run_rocs_frequency(expanded_file, output_dir)

    if not args.save and os.path.exists(EXPANDED_INPUT_FILE):
        os.remove(EXPANDED_INPUT_FILE)

    print(f"Plots saved to: {output_dir}")

if __name__ == "__main__":
    main()