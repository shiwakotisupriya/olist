"""Create and execute the reproducible approval-time modelling notebook."""
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

ROOT=Path(__file__).resolve().parents[1]

def main():
    nb=nbf.v4.new_notebook()
    nb.metadata.kernelspec={'display_name':'Python 3','language':'python','name':'python3'}
    nb.cells=[
        nbf.v4.new_markdown_cell('# Approval-time late-delivery prediction\n\n## tl;dr\nLogistic regression was selected using validation average precision. On July–August 2018 test approvals, investigating its top 10% identifies 124 of 599 late deliveries from 1,255 investigations (9.88% precision; 20.70% recall). Random ranking would identify approximately 60 late deliveries at the same budget. The fixed validation threshold flags 31.95% of test orders, exposing workload drift. This is a historical portfolio experiment, not a deployed service.'),
        nbf.v4.new_markdown_cell('## Context & Methods\nPredict late delivery at order approval in historical Brazilian Olist data. Late means the actual delivery calendar date is after the promised calendar date. Compare a constant-prevalence baseline, logistic regression and gradient boosting. PR-AUC uses **average precision**, not trapezoidal integration. Select the model using validation AP, then freeze the model and threshold before testing.\n\n### Key Assumptions\nItem, price, freight, product and seller snapshot attributes are assumed available and unchanged at approval; Olist has no attribute version history. No delivery outcomes, reviews, carrier dates or later status enter features. Only delivered orders with observed outcomes are labelled; unresolved/cancelled orders are outside scope. First-item seller state/category represent multi-item orders. Staffing budgets of 5%, 10%, 20% are case-study assumptions.\n\nTrain: approvals before January 2018, with delivery labels available before January. Validation: January–June 2018 approvals, labels available before July. Test: July–August 2018 approvals. Purging unavailable labels reduces leakage but may introduce boundary selection bias. Test cohorts may have unequal outcome follow-up.'),
        nbf.v4.new_code_cell("from pathlib import Path\nimport sys, io, contextlib, json\nimport pandas as pd\nfrom IPython.display import display, Image\nROOT = Path.cwd()\nif ROOT.name == 'notebooks': ROOT = ROOT.parent\nassert (ROOT / 'python').exists(), 'Run from the project root or notebooks folder'\nsys.path.insert(0, str(ROOT / 'python'))\nimport train_models\nprint('Features:', ', '.join(train_models.FEATURES))"),
        nbf.v4.new_markdown_cell('## Data\nInputs are generated reproducibly by `python/build_analysis.py` from the nine original CSVs in `data/raw`. SHA-256 source hashes and SQL reconciliation checks are stored in `docs/analysis_checks.json`. The model consumes only the explicit feature whitelist above. `is_late` and actual delivery dates are retained for labels and chronological label-availability purging, never for prediction.'),
        nbf.v4.new_code_cell("if not (ROOT/'data/processed/model_input.csv').exists():\n    import build_analysis\n    with contextlib.redirect_stdout(io.StringIO()): build_analysis.main()\nsource = pd.read_csv(ROOT/'data/processed/model_input.csv')\nprint(f'{len(source):,} source orders; columns include labels and audit fields as well as features.')\ndisplay(source[train_models.FEATURES].head(3).T.rename_axis('Feature'))"),
        nbf.v4.new_markdown_cell('## Results\n### Chronological evaluation\nPreprocessing is fitted on training data only. The model with highest validation AP is selected; test outcomes do not select a model or threshold. A model threshold is set to the validation 90th percentile. The constant baseline uses 0.5 and therefore flags no orders; the separate capacity table gives its random-ranking expectation.'),
        nbf.v4.new_code_cell("with contextlib.redirect_stdout(io.StringIO()):\n    metrics, capacity, audit = train_models.main()\ndisplay(pd.DataFrame(audit['splits']).T)\nprint('Selected model:', audit['selected_model'])\ndisplay(metrics.round(4))"),
        nbf.v4.new_code_cell("display(Image(filename=str(ROOT/'docs/figures/model_pr.png')))"),
        nbf.v4.new_markdown_cell('### Investigation workload\nFixed-budget rankings are retrospective test simulations at predetermined capacities; outcomes are used only to evaluate the ranking. A constant score has no ranking power, so its budget performance is a mathematical random-selection expectation rather than a fabricated observed ranking.'),
        nbf.v4.new_code_cell("display(capacity.round(4))\nchosen = capacity[(capacity.model == audit['selected_model']) & (capacity.budget_fraction == .10)].iloc[0]\nprint(f\"Investigate {int(chosen.investigated):,} orders to find {int(chosen.late_found):,} late orders: {chosen.investigations_per_late:.2f} investigations per late order.\")"),
        nbf.v4.new_markdown_cell('## Takeaways\nThe selected model improves ranking over random selection but misses most late deliveries at a 10% budget. Its test AP is about 0.092 versus a 0.048 prevalence baseline. Precision remains low: approximately nine of ten flagged orders at that budget are on time. Gradient boosting does not outperform logistic regression on validation AP.\n\nUse the queue as a simulated prioritisation aid, with human investigation and capacity limits. Do not claim reduced delays, saved revenue or deployment readiness. Investigate calibration, temporal drift and route/seller interactions in a new validation period before changing the model; preserve this test set as a final historical evaluation. `docs/model_audit.json` records exclusions and assumptions. `data/processed/historical_priority_queue.csv` is historical, not a live operational queue.')
    ]
    path=ROOT/'notebooks/late_delivery_prediction.ipynb'
    path.parent.mkdir(parents=True,exist_ok=True)
    nbf.validate(nb)
    NotebookClient(nb,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(ROOT)}}).execute()
    nbf.write(nb,path)
    print('Executed and saved',path)

if __name__=='__main__':main()
