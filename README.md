
# Automasked ROC Frequency Plotter

This tool processes time-resolved automasking data for Pixel ROCs in the CMS detector, computes the **frequency of masking** across a complete fill, and generates 2D digiplots to visualize the results. It also prints a **summary table** showing how many ROCs were automasked and blacklisted per detector layer.

---

## Script Location

```
/pixel/users/Calibrations/automasked_frequency_plots/
```

---

## Workflow

### 1. Get Fill Info from CMSOMS

Visit [CMSOMS](https://cmsoms.cern.ch/) to find the **start** and **end times** of the **stable beams** period for your fill. Also note the **fill number**.

The script pulls input data from:

```
/nfspixelraid/nfspixelraid/users/masks/automasked_channels/
```

### 2. Log In and Set Up

```bash
ssh srv-s2b18-31-01
sudo -u pixelpro -H zsh -l

cd /nfshome0/pixelpro/TriDAS
source setenv.sh
cd /pixel/users/Calibrations/automasked_frequency_plots
```

### 3. Run the Script



#### Basic usage:

```bash
python3 plot_rocs_summary.py --fill <FILL> --start "YYYY-MM-DD HH:MM:SS" --end "YYYY-MM-DD HH:MM:SS"
```

#### Optional flags:

- `-blacklisted` – Only include ROCs that were blacklisted.
  - Output will be saved under:  
    `/pixel/users/Calibrations/automasked_frequency_plots/fill_<FILL>/blacklisted/`
- `-save` – Save the expanded ROC list used for the plots.

---

## Example

```bash
python3 plot_rocs_summary.py --fill 10674 \
  --start "2025-05-29 21:23:54" \
  --end "2025-05-30 03:34:24" -save
```

---

## Output

Output is saved to:

```
/pixel/users/Calibrations/automasked_frequency_plots/fill_<FILL>/
```

If `-blacklisted` is used:

```
/pixel/users/Calibrations/automasked_frequency_plots/fill_<FILL>/blacklisted/
```

Includes:
- ROC frequency plots (`PXBarrel_LayerX.png`, `PXForward_RingX.png`)
- Printed summary table (see below)
- (Optional) expanded input list (`fill_<FILL>.dat`)

---

## Summary Output (Example)

```
================================================================================
                                   SUMMARY                                    
================================================================================
Layer        Masked    Total    % Automasked    Blacklisted   % Blacklisted
--------------------------------------------------------------------------------
BPix L1         36      1536          2.34%              2           0.26%
BPix L2         76      3584          2.12%             16           1.79%
BPix L3         32      5632          0.57%              1           0.14%
BPix L4         64      8192          0.78%              8           0.78%
FPix D1         16      3584          0.45%              1           0.22%
FPix D2         24      3584          0.67%              3           0.67%
FPix D3         96      3584          2.68%              7           1.56%
--------------------------------------------------------------------------------
Total          344     29696          1.16%             38           0.80%
```

---

## Authors

- Script & Analysis: Athar Ahmad  
