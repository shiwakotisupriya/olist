"""Chronological approval-time comparison; no outcome columns enter X."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_score, recall_score, precision_recall_curve

ROOT=Path(__file__).resolve().parents[1]
NUM=['merchandise_value','freight_value','item_count','seller_count','total_weight_g','max_length_cm','max_height_cm','max_width_cm','promised_days','approval_hour','approval_weekday','same_state']
CAT=['customer_state','seller_state','category_key']
FEATURES=NUM+CAT

def metrics(y, probability, threshold):
    prediction=probability>=threshold
    tp=int(((y==1)&prediction).sum()); n=int(prediction.sum())
    return {'average_precision':float(average_precision_score(y,probability)),
        'precision':float(precision_score(y,prediction,zero_division=0)),
        'recall':float(recall_score(y,prediction,zero_division=0)),
        'investigated':n,'late_found':tp,'investigations_per_late':n/tp if tp else None,
        'investigation_fraction':float(prediction.mean()),'threshold':float(threshold)}

def main():
    source=pd.read_csv(ROOT/'data/processed/model_input.csv',parse_dates=['order_approved_at','order_delivered_customer_date'])
    eligible=source.delivery_eligible.eq(1)&source.order_approved_at.notna()&source.promised_days.ge(0)
    frame=source.loc[eligible].sort_values(['order_approved_at','order_id']).copy()
    # Outcome availability purge: training labels must exist when validation starts,
    # and validation labels must exist before the frozen model is tested in July.
    trainmask=frame.order_approved_at.lt('2018-01-01')&frame.order_delivered_customer_date.lt('2018-01-01')
    valmask=frame.order_approved_at.ge('2018-01-01')&frame.order_approved_at.lt('2018-07-01')&frame.order_delivered_customer_date.lt('2018-07-01')
    testmask=frame.order_approved_at.ge('2018-07-01')&frame.order_approved_at.lt('2018-09-01')
    splits={'train':frame.loc[trainmask], 'validation':frame.loc[valmask], 'test':frame.loc[testmask]}
    assert set(FEATURES).isdisjoint({'is_late','order_delivered_customer_date','delivery_eligible','review_score'})
    assert splits['train'].order_delivered_customer_date.max()<pd.Timestamp('2018-01-01')
    assert splits['validation'].order_delivered_customer_date.max()<pd.Timestamp('2018-07-01')
    assert all(len(x)>0 and x.is_late.nunique()==2 for x in splits.values())
    numeric=Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())])
    category=Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),('encode',OneHotEncoder(handle_unknown='ignore',min_frequency=30))])
    pre=ColumnTransformer([('numeric',numeric,NUM),('category',category,CAT)])
    treepre=ColumnTransformer([('numeric',SimpleImputer(strategy='median',add_indicator=True),NUM),
        ('category',Pipeline([('impute',SimpleImputer(strategy='constant',fill_value='Unknown')),('encode',OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1))]),CAT)])
    models={'Prevalence baseline':DummyClassifier(strategy='prior'),
        'Logistic regression':Pipeline([('preprocess',pre),('model',LogisticRegression(max_iter=1500,random_state=42))]),
        'Gradient boosting':Pipeline([('preprocess',treepre),('model',HistGradientBoostingClassifier(max_iter=150,max_leaf_nodes=15,l2_regularization=2,learning_rate=.07,early_stopping=False,random_state=42))])}
    # Ordinal codes represent nominal categories; tell the tree estimator explicitly.
    # Determine transformed column count after fitting the tree preprocessor on train only.
    treepre.fit(splits['train'][FEATURES])
    nnum=treepre.named_transformers_['numeric'].transform(splits['train'][NUM]).shape[1]
    models['Gradient boosting'].named_steps['model'].set_params(categorical_features=list(range(nnum,nnum+len(CAT))))
    rows=[]; scores={}; probs={}
    for name,model in models.items():
        model.fit(splits['train'][FEATURES],splits['train'].is_late.astype(int))
        for split in ['validation','test']:
            probs[name,split]=model.predict_proba(splits[split][FEATURES])[:,1]
        scores[name]=float(average_precision_score(splits['validation'].is_late,probs[name,'validation']))
    selected=max(scores,key=scores.get)
    # Model and threshold selected only from validation. Baseline has no ranking power;
    # apply its conventional .5 cutoff and report random-budget expectation separately.
    for name in models:
        threshold=.5 if name=='Prevalence baseline' else float(np.quantile(probs[name,'validation'],.90))
        for split in ['validation','test']:
            row={'model':name,'split':split,**metrics(splits[split].is_late.astype(int).to_numpy(),probs[name,split],threshold)}
            rows.append(row)
    out=ROOT/'data/processed'
    pd.DataFrame(rows).to_csv(out/'model_metrics.csv',index=False)
    budget=[]
    for name in models:
        y=splits['test'].is_late.astype(int).to_numpy(); p=probs[name,'test']
        for fraction in [.05,.10,.20]:
            count=int(np.ceil(len(y)*fraction))
            if name=='Prevalence baseline':
                found=count*y.mean();kind='Random ranking expectation'
            else:
                # Exact budget simulation using outcomes only for retrospective evaluation.
                rank=np.argsort(-p,kind='stable')[:count];found=int(y[rank].sum());kind='Observed test ranking'
            budget.append({'model':name,'budget_fraction':fraction,'investigated':count,'late_found':found,
                'precision':found/count,'recall':found/y.sum(),'investigations_per_late':count/found if found else None,'kind':kind})
    pd.DataFrame(budget).to_csv(out/'capacity_tradeoff.csv',index=False)
    prediction=splits['test'][['order_id','order_approved_at','is_late']].copy()
    prediction['risk_score']=probs[selected,'test']
    prediction.sort_values(['risk_score','order_id'],ascending=[False,True]).to_csv(out/'historical_priority_queue.csv',index=False)
    audit={'prediction_point':'Order approval','features':FEATURES,'selected_model':selected,
        'selection_rule':'Highest validation average precision; test untouched until evaluation',
        'splits':{k:{'orders':len(v),'late':int(v.is_late.sum()),'late_rate':float(v.is_late.mean()),
            'first_approval':str(v.order_approved_at.min()),'last_approval':str(v.order_approved_at.max())} for k,v in splits.items()},
        'excluded_noneligible_missing_approval_or_negative_promise':int((~eligible).sum()),
        'train_labels_unavailable_at_validation_start':int((frame.order_approved_at.lt('2018-01-01')&~trainmask).sum()),
        'validation_labels_unavailable_at_test_start':int((frame.order_approved_at.ge('2018-01-01')&frame.order_approved_at.lt('2018-07-01')&~valmask).sum()),
        'assumptions':['Item prices, freight and product/seller attributes represent their approval-time values; this snapshot has no change history.',
            'Only delivered orders with observable outcomes are modelled; results do not cover cancellations or unresolved shipments.',
            'Latest test cohorts may have unequal outcome observation; no claim of live deployment performance.',
            '10% validation investigation fraction is a case-study staffing assumption; test volume may differ at the frozen threshold.',
            'Numeric missingness and unknown categories handled by training-fitted preprocessing; no future seller performance aggregates.',
            'First item determines representative seller state/category for multi-item orders; this is a lossy simplification.',
            'PR-AUC is reported as sklearn average precision, not trapezoidal integration.']}
    (ROOT/'docs/model_audit.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    fig,ax=plt.subplots(figsize=(8,5))
    for name in models:
        if name=='Prevalence baseline':
            ax.axhline(splits['test'].is_late.mean(),color='#555555',linestyle='--',label=f'Random ranking / prevalence ({splits["test"].is_late.mean():.3f})')
            continue
        precision,recall,_=precision_recall_curve(splits['test'].is_late,probs[name,'test'])
        ax.step(recall,precision,where='post',label=f'{name} (AP {average_precision_score(splits["test"].is_late,probs[name,"test"]):.3f})')
    ax.set(xlim=(0,1),ylim=(0,1),xlabel='Recall of late orders',ylabel='Precision among investigated orders',title='Later-order test: precision–recall trade-off');ax.legend();fig.tight_layout();fig.savefig(ROOT/'docs/figures/model_pr.png',dpi=150);plt.close(fig)
    print(json.dumps(audit,indent=2));print(pd.DataFrame(rows).to_string(index=False));print(pd.DataFrame(budget).to_string(index=False))
    return pd.DataFrame(rows),pd.DataFrame(budget),audit

if __name__=='__main__':main()
