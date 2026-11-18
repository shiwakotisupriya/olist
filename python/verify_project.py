"""Check material reporting invariants, model accounting and local deliverable links."""
from pathlib import Path
import json
import re
import numpy as np
import pandas as pd
import nbformat

ROOT=Path(__file__).resolve().parents[1]

def main():
    f=pd.read_csv(ROOT/'data/processed/order_fact.csv')
    items=pd.read_csv(ROOT/'data/processed/report_items.csv')
    categories=pd.read_csv(ROOT/'data/processed/order_category.csv')
    result={}
    assert f.order_id.is_unique and len(f)==99441
    assert f.query('is_delivered == 1').merchandise_value.sum().round(2)==13221498.11
    assert len(f.query('delivery_eligible == 1'))==96470
    for state,n,late in [('RJ',12350,1495),('SP',40494,1820)]:
        s=f[f.customer_state.eq(state)&f.delivery_eligible.eq(1)]
        assert len(s)==n and s.is_late.sum()==late
    audio_ids=categories.loc[categories.category_key.eq('audio'),'order_id']
    selected=f[f.order_id.isin(audio_ids)&f.delivery_eligible.eq(1)]
    assert len(selected)==348 and selected.is_late.sum()==41
    # Date+category case: demonstrate order-set filtering and selected-item attribution.
    month='2018-01'
    selected=f[f.order_id.isin(audio_ids)&f.month.eq(month)&f.delivery_eligible.eq(1)]
    audio_items=items[items.category_key.eq('audio')&items.order_id.isin(f.loc[f.month.eq(month)&f.is_delivered.eq(1),'order_id'])]
    result['audio_january_2018']={'eligible':len(selected),'late':int(selected.is_late.sum()),'selected_item_merchandise_brl':round(float(audio_items.price.sum()),2)}
    monthly=pd.read_csv(ROOT/'data/processed/monthly.csv')
    assert len(monthly)==26 and monthly.loc[monthly.month.eq('2016-11'),'orders'].iloc[0]==0
    assert pd.isna(monthly.loc[monthly.month.eq('2016-12'),'growth_fraction'].iloc[0])
    result['calendar_spine']='26 consecutive months; growth after zero denominator is blank'
    metrics=pd.read_csv(ROOT/'data/processed/model_metrics.csv')
    budget=pd.read_csv(ROOT/'data/processed/capacity_tradeoff.csv')
    audit=json.loads((ROOT/'docs/model_audit.json').read_text())
    row=budget[budget.model.eq(audit['selected_model'])&budget.budget_fraction.eq(.10)].iloc[0]
    assert row.investigated==1255 and row.late_found==124
    assert sum(v['orders'] for v in audit['splits'].values())+audit['excluded_noneligible_missing_approval_or_negative_promise']+audit['train_labels_unavailable_at_validation_start']+audit['validation_labels_unavailable_at_test_start']==99441
    for r in metrics.itertuples():
        assert r.late_found<=r.investigated
        if r.late_found:assert np.isclose(r.investigations_per_late,r.investigated/r.late_found)
    nb=nbformat.read(ROOT/'notebooks/late_delivery_prediction.ipynb',as_version=4)
    nbformat.validate(nb)
    code=[c for c in nb.cells if c.cell_type=='code']
    assert all(c.execution_count is not None for c in code)
    assert not any(o.output_type=='error' for c in code for o in c.outputs)
    assert any('image/png' in o.get('data',{}) for c in code for o in c.outputs)
    result['notebook']={'executed_code_cells':len(code),'errors':0,'inline_figure':True}
    missing=[]
    for path in [ROOT/'README.md',*sorted((ROOT/'docs').glob('*.md')),ROOT/'powerbi/README.md']:
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf8')):
            if '://' in target or target.startswith('#'):continue
            dest=(path.parent/target.split('#')[0])
            if not dest.exists():missing.append(str(path.relative_to(ROOT))+': '+target)
    assert not missing,missing
    result['local_markdown_links']='All checked destinations exist'
    result['powerbi']=json.loads((ROOT/'powerbi/validation.json').read_text())
    result['limitations']=['Power BI Desktop refresh, DAX and interactions are unverified.',
        'Revised monthly SQL calendar spine was not rerun in MySQL.',
        'No video recording or remote GitHub publication was performed.']
    (ROOT/'docs/final_verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
