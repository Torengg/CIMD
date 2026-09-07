# Discount-framing A/B test

This Streamlit application collects responses for a blinded, between-subjects marketing experiment. Each participant is randomly assigned once to one of the two original ad creatives and sees only that creative:

- **A:** 20% OFF
- **B:** SAVE ₹500 TODAY

The product and final price are unchanged (₹2,500 → ₹2,000). The app does not disclose the A/B comparison or the hypothesis to participants.

## Run locally

1. Open a terminal in this folder.
2. Create and activate a virtual environment (recommended):

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the libraries:

   ```powershell
   pip install -r requirements.txt
   ```

4. Start the data-collection app:

   ```powershell
   streamlit run app.py
   ```

Streamlit will display a local URL, normally `http://localhost:8501`. Open it in a browser and share it only after deploying the app if participants are remote.

## Responses and privacy

Every completed response is appended to `data/responses.csv`. It contains a generated respondent ID, optional participant ID, UTC timestamp, assigned group, controls, the three purchase-intention ratings, manipulation checks, and the automatically calculated Purchase Intention Index (PII):

`(purchase likelihood + purchase consideration + offer choice likelihood) / 3`

Do not open or share this CSV with participants. It is the researcher data file; the participant app never displays its contents.

## Analyse the collected data

After at least two valid responses in each group, run:

```powershell
python analysis.py
```

It prints group sample sizes, mean PII, standard deviations, the independent-samples t-test, p-value, Cohen's d, and a conclusion using α = .05. Cohen's d and the mean difference are signed **A − B**, so positive values favour the percentage-framed offer.

## Creative files

- `ads/source_combined_creative.png` is the untouched uploaded original.
- `ads/version_a.png` and `ads/version_b.png` are clean crops used by the app. They intentionally exclude the labels that identify the two versions and the comparison slogan from the uploaded combined image.

If you receive separate final creatives later, replace only `ads/version_a.png` and `ads/version_b.png` while keeping their filenames.
