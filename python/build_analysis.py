"""Rebuild validated order-grain analysis and Power BI inputs from original CSVs."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'data' / 'processed'
FIG = ROOT / 'docs' / 'figures'

def load(name):
    return pd.read_csv(ROOT / 'data' / 'raw' / (name + '.csv'))

def save(df, name):
    df.to_csv(OUT / (name + '.csv'), index=False)

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    orders = load('olist_orders_dataset')
    customers = load('olist_customers_dataset')
    items = load('olist_order_items_dataset')
    payments = load('olist_order_payments_dataset')
    reviews = load('olist_order_reviews_dataset')
    products = load('olist_products_dataset')
    sellers = load('olist_sellers_dataset')
    trans = load('product_category_name_translation')
    for frame in [orders, reviews]:
        for c in frame.columns:
            if c.endswith('_timestamp') or c.endswith('_date') or c == 'order_approved_at':
                frame[c] = pd.to_datetime(frame[c], errors='raise')
    for frame, keys in [(orders,['order_id']), (customers,['customer_id']),
                        (items,['order_id','order_item_id']), (payments,['order_id','payment_sequential']),
                        (products,['product_id']), (sellers,['seller_id'])]:
        assert not frame.duplicated(keys).any(), keys
    assert reviews.review_score.between(1,5).all()
    ia = items.groupby('order_id').agg(item_count=('order_item_id','size'),
        seller_count=('seller_id','nunique'), merchandise_value=('price','sum'), freight_value=('freight_value','sum')).reset_index()
    pa = payments.groupby('order_id').agg(payment_value=('payment_value','sum')).reset_index()
    selected = reviews.sort_values(['order_id','review_creation_date','review_answer_timestamp','review_id','review_score']).drop_duplicates('order_id', keep='last')
    f = orders.merge(customers[['customer_id','customer_unique_id','customer_state']], on='customer_id', how='left', validate='many_to_one')
    for frame in [ia,pa,selected[['order_id','review_score','review_creation_date','review_answer_timestamp']]]:
        f = f.merge(frame,on='order_id',how='left',validate='one_to_one')
    f['purchase_date'] = f.order_purchase_timestamp.dt.normalize()
    f['month'] = f.purchase_date.dt.to_period('M').astype(str)
    f['is_delivered'] = (f.order_status == 'delivered').astype(int)
    f['delivery_eligible'] = (f.is_delivered.eq(1) & f.order_delivered_customer_date.notna() & f.order_estimated_delivery_date.notna()).astype(int)
    f['is_late'] = np.where(f.delivery_eligible.eq(1), (f.order_delivered_customer_date.dt.normalize() > f.order_estimated_delivery_date.dt.normalize()).astype(int), np.nan)
    duration = (f.order_delivered_customer_date-f.order_purchase_timestamp).dt.total_seconds()/86400
    f['delivery_days'] = duration.where(f.is_delivered.eq(1) & duration.ge(0))
    f['review_eligible'] = f.review_score.between(1,5).astype(int)
    f['low_review'] = np.where(f.review_eligible.eq(1), f.review_score.le(2).astype(int), np.nan)
    f['delivery_outcome'] = f.is_late.map({0:'On time',1:'Late'}).fillna('Not eligible')
    assert len(f) == f.order_id.nunique() == 99441
    assert f.is_delivered.sum() == 96478 and f.delivery_eligible.sum() == 96470 and f.is_late.sum() == 6534
    d = f[f.is_delivered.eq(1)].copy()
    raw_delivered = items[items.order_id.isin(d.order_id)]
    assert round(d.merchandise_value.sum(),2) == round(raw_delivered.price.sum(),2) == 13221498.11
    assert round(d.freight_value.sum(),2) == round(raw_delivered.freight_value.sum(),2) == 2198275.64
    assert round(f.payment_value.sum(),2) == round(payments.payment_value.sum(),2)
    save(f,'order_fact')
    monthly = d.groupby('month').agg(orders=('order_id','size'),merchandise_brl=('merchandise_value','sum'),freight_brl=('freight_value','sum'))
    monthly = monthly.reindex(pd.period_range(f.purchase_date.min(), f.purchase_date.max(),freq='M').astype(str),fill_value=0)
    monthly.index.name='month'
    monthly['aov_brl']=monthly.merchandise_brl/monthly.orders.replace(0,np.nan)
    monthly['growth_fraction']=monthly.merchandise_brl.pct_change(fill_method=None).where(monthly.merchandise_brl.shift().gt(0))
    save(monthly.reset_index(),'monthly')
    e=f[f.delivery_eligible.eq(1)]
    def compare(frame, key):
        return frame.groupby(key,dropna=False).agg(eligible_orders=('order_id','size'),late_orders=('is_late','sum'),late_rate=('is_late','mean'),mean_delivery_days=('delivery_days','mean')).reset_index()
    regions=compare(e,'customer_state').sort_values('late_orders',ascending=False)
    regions['late_orders_above_overall_rate']=regions.late_orders-regions.eligible_orders*e.is_late.mean()
    save(regions,'regions')
    os=items.groupby(['order_id','seller_id']).agg(seller_merchandise_value=('price','sum'),seller_freight_value=('freight_value','sum')).reset_index()
    save(os,'order_seller')
    seller_stats=compare(os.merge(e,on='order_id',validate='many_to_one'),'seller_id').sort_values(['late_rate','eligible_orders'],ascending=False)
    seller_stats['meets_minimum']=seller_stats.eligible_orders.ge(100)
    save(seller_stats,'sellers')
    ip=items.merge(products,on='product_id',how='left',validate='many_to_one')
    ip['category_key']=ip.product_category_name.fillna('__UNKNOWN__')
    oc=ip.groupby(['order_id','category_key']).agg(category_merchandise_value=('price','sum')).reset_index()
    save(oc,'order_category')
    categories=compare(oc.merge(e,on='order_id',validate='many_to_one'),'category_key').merge(trans,left_on='category_key',right_on='product_category_name',how='left',validate='many_to_one')
    categories['category_label']=categories.product_category_name_english.fillna(categories.category_key)
    categories=categories.sort_values(['late_rate','eligible_orders'],ascending=False)
    save(categories,'categories')
    dimcat=oc[['category_key']].drop_duplicates().merge(trans,left_on='category_key',right_on='product_category_name',how='left',validate='one_to_one')
    dimcat['category_label']=dimcat.product_category_name_english.fillna(dimcat.category_key)
    save(dimcat[['category_key','category_label']],'dim_category')
    review=e.groupby('delivery_outcome').agg(eligible_orders=('order_id','size'),reviewed_orders=('review_eligible','sum'),mean_review_score=('review_score','mean'),low_review_rate=('low_review','mean')).reset_index()
    review['review_coverage']=review.reviewed_orders/review.eligible_orders
    save(review,'review_comparison')
    save(d[d.review_eligible.eq(1)].groupby('review_score').size().rename('orders').reset_index(),'review_distribution')
    save(compare(e,'month'),'monthly_delivery')
    calendar=pd.DataFrame({'Date':pd.date_range(f.purchase_date.min(),f.purchase_date.max())})
    calendar['Year']=calendar.Date.dt.year
    calendar['Month']=calendar.Date.dt.strftime('%Y-%m')
    calendar['MonthNumber']=calendar.Date.dt.month
    save(calendar,'dim_date')
    # Independently recomputed values must match the owner's exported MySQL results.
    reconciled={}
    for number,new,key,cols in [(2,monthly.reset_index(),'month',['orders','merchandise_brl','freight_brl']),
        (5,seller_stats,'seller_id',['eligible_orders','late_orders','late_rate']),
        (6,categories,'category_key',['eligible_orders','late_orders','late_rate']),
        (10,regions,'customer_state',['eligible_orders','late_orders','late_rate'])]:
        path=ROOT/'sql'/f'result{number}.csv'
        if path.exists():
            old=pd.read_csv(path)
            if key=='month': old[key]=old[key].str[:7]
            joined=old.merge(new,on=key,suffixes=('_sql','_python'),validate='one_to_one')
            assert len(joined)==len(old)
            for col in cols:
                assert np.allclose(joined[col+'_sql'],joined[col+'_python'],atol=0.000051 if 'rate' in col else 0.011,rtol=0), (number,col)
            reconciled[str(number)]={'rows':len(old),'matched':True,'columns_checked':cols}
    old=pd.read_csv(ROOT/'sql'/'result9.csv')
    check=e.groupby('is_late').agg(eligible_orders=('order_id','size'),reviewed_orders=('review_eligible','sum')).reset_index()
    pd.testing.assert_frame_equal(old[['eligible_orders','reviewed_orders']].reset_index(drop=True),check[['eligible_orders','reviewed_orders']],check_dtype=False)
    reconciled['9']={'rows':len(old),'matched':True}
    # Portable notebook/model inputs. Only explicit approved-time features are used later.
    ip=ip.merge(sellers[['seller_id','seller_state']],on='seller_id',validate='many_to_one')
    primary=ip.sort_values(['order_id','order_item_id']).drop_duplicates('order_id')[['order_id','seller_state','category_key']]
    attrs=ip.groupby('order_id').agg(total_weight_g=('product_weight_g',lambda x:x.sum(min_count=1)),
        max_length_cm=('product_length_cm','max'),max_height_cm=('product_height_cm','max'),max_width_cm=('product_width_cm','max'))
    model=f.merge(primary,on='order_id',how='left',validate='one_to_one').merge(attrs,on='order_id',how='left',validate='one_to_one')
    model['promised_days']=(model.order_estimated_delivery_date-model.order_approved_at).dt.total_seconds()/86400
    model['approval_hour']=model.order_approved_at.dt.hour
    model['approval_weekday']=model.order_approved_at.dt.dayofweek
    model['same_state']=(model.customer_state==model.seller_state).astype(int)
    modelcols=['order_id','order_approved_at','order_delivered_customer_date','delivery_eligible','is_late',
        'merchandise_value','freight_value','item_count','seller_count','total_weight_g','max_length_cm','max_height_cm','max_width_cm',
        'promised_days','approval_hour','approval_weekday','same_state','customer_state','seller_state','category_key']
    save(model[modelcols],'model_input')
    quality={'row_count':len(f),'delivered':len(d),'eligible':len(e),'late':int(e.is_late.sum()),
        'merchandise_brl':round(d.merchandise_value.sum(),2),'freight_brl':round(d.freight_value.sum(),2),
        'aov_brl':float(d.merchandise_value.sum()/len(d)),'late_rate':float(e.is_late.mean()),
        'review_created_before_delivery':int((d.review_creation_date<d.order_delivered_customer_date).sum()),
        'negative_item_prices':int(items.price.lt(0).sum()),'negative_freight':int(items.freight_value.lt(0).sum()),
        'sql_exports_reconciled':reconciled,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'data'/'raw').glob('*.csv'))}}
    (ROOT/'docs'/'analysis_checks.json').write_text(json.dumps(quality,indent=2),encoding='utf8')
    plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'white'})
    period=monthly.loc['2017-01':'2018-08']
    fig,ax=plt.subplots(figsize=(11,4.5)); ax.plot(period.index,period.merchandise_brl/1e6,color='#116B83',marker='o')
    ax.set(title='Delivered-order merchandise value by purchase month',ylabel='BRL millions',xlabel='Purchase month (historical Brazil)');ax.tick_params(axis='x',rotation=60);ax.set_ylim(bottom=0);fig.tight_layout();fig.savefig(FIG/'monthly_value.png',dpi=150);plt.close(fig)
    top=regions.head(10).iloc[::-1]
    fig,ax=plt.subplots(figsize=(9,5));ax.barh(top.customer_state,top.late_orders,color='#116B83');ax.set(title='Late-order volume by customer state',xlabel='Late delivered orders (both dates present)');fig.tight_layout();fig.savefig(FIG/'region_volume.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4));ax.bar(review.delivery_outcome,review.low_review_rate*100,color=['#C85A3B' if x=='Late' else '#116B83' for x in review.delivery_outcome]);ax.set(title='Low reviews are more frequent on late orders',ylabel='Reviewed eligible orders rated 1–2 (%)',ylim=(0,100))
    for x,v in enumerate(review.low_review_rate*100): ax.text(x,v+2,f'{v:.2f}%',ha='center')
    fig.tight_layout();fig.savefig(FIG/'review_gap.png',dpi=150);plt.close(fig)
    print(json.dumps({k:v for k,v in quality.items() if k!='source_sha256'},indent=2))

if __name__=='__main__': main()
