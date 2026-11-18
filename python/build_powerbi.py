"""Generate an editable three-page PBIP/PBIR report and import-mode model.

Uses Microsoft's public PBIR schemas. Desktop refresh/visual QA is separate.
"""
from pathlib import Path
import json
import uuid
import pandas as pd
from jsonschema import Draft7Validator, RefResolver

ROOT=Path(__file__).resolve().parents[1]
PBI=ROOT/'powerbi'
BASE='https://developer.microsoft.com/json-schemas/fabric/item/'

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf8')

def field(table,name,measure=False):
    return {'Measure' if measure else 'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}

def literal(value):
    if isinstance(value,bool): value='true' if value else 'false'
    elif isinstance(value,(int,float)):value=str(value)
    else:value="'"+value.replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':value}}}

def main():
    report=PBI/'Olist.Report'; model=PBI/'Olist.SemanticModel'
    items=pd.read_csv(ROOT/'data/raw/olist_order_items_dataset.csv')
    products=pd.read_csv(ROOT/'data/raw/olist_products_dataset.csv')
    items=items.merge(products[['product_id','product_category_name']],on='product_id',validate='many_to_one')
    items['category_key']=items.product_category_name.fillna('__UNKNOWN__')
    items[['order_id','seller_id','category_key','price','freight_value']].to_csv(ROOT/'data/processed/report_items.csv',index=False)
    sellers=pd.read_csv(ROOT/'data/raw/olist_sellers_dataset.csv')[['seller_id','seller_state']]
    sellers['seller_label']=sellers.seller_id.str[:8]+' ('+sellers.seller_state+')'
    assert sellers.seller_label.is_unique
    sellers.to_csv(ROOT/'data/processed/dim_seller.csv',index=False)
    write(PBI/'Olist.pbip',{'version':'1.0','artifacts':[{'report':{'path':'Olist.Report'}}],'settings':{'enableAutoRecovery':True}})
    write(report/'definition.pbir',{'$schema':BASE+'report/definitionProperties/2.0.0/schema.json','version':'4.0','datasetReference':{'byPath':{'path':'../Olist.SemanticModel'}}})
    write(model/'definition.pbism',{'$schema':BASE+'semanticModel/definitionProperties/1.0.0/schema.json','version':'1.0','settings':{}})
    specs={
        'Orders':('order_fact',{'order_id':'string','purchase_date':'dateTime','month':'string','customer_state':'string','is_delivered':'int64','delivery_eligible':'int64','is_late':'int64','delivery_days':'double','review_score':'int64','review_eligible':'int64','low_review':'int64','delivery_outcome':'string'}),
        'Items':('report_items',{'order_id':'string','seller_id':'string','category_key':'string','price':'double','freight_value':'double'}),
        'Calendar':('dim_date',{'Date':'dateTime','Year':'int64','Month':'string','MonthNumber':'int64'}),
        'Categories':('dim_category',{'category_key':'string','category_label':'string'}),
        'Sellers':('dim_seller',{'seller_id':'string','seller_state':'string','seller_label':'string'}),
    }
    tables=[]
    for name,(filename,columns) in specs.items():
        csvpath=(ROOT/'data/processed'/f'{filename}.csv').as_posix()
        mtypes={'string':'type text','dateTime':'type datetime','int64':'Int64.Type','double':'type number'}
        conversions=', '.join('{"'+c+'", '+mtypes[t]+'}' for c,t in columns.items())
        expr=['let',f'    Source = Csv.Document(File.Contents("{csvpath}"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            '    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),',
            '    EmptyToNull = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
            '    Selected = Table.SelectColumns(EmptyToNull, {'+', '.join('"'+c+'"' for c in columns)+'}),',
            '    Typed = Table.TransformColumnTypes(Selected, {'+conversions+'}, "en-US")','in','    Typed']
        table={'name':name,'columns':[{'name':c,'dataType':t,'sourceColumn':c,'summarizeBy':'none',**({'formatString':'yyyy-MM-dd'} if t=='dateTime' else {})} for c,t in columns.items()],
            'partitions':[{'name':name,'mode':'import','source':{'type':'m','expression':expr}}]}
        tables.append(table)
    scope='KEEPFILTERS(TREATAS(VALUES(Items[order_id]), Orders[order_id]))'
    measures={
        'Delivered Orders':(f'CALCULATE(DISTINCTCOUNT(Orders[order_id]), Orders[is_delivered] = 1, {scope})','#,0','Distinct delivered orders containing selected items.'),
        'Merchandise BRL':('CALCULATE(SUM(Items[price]), Orders[is_delivered] = 1)','"BRL "#,0.00','Item prices in delivered orders; selected category/seller attribution.'),
        'Freight BRL':('CALCULATE(SUM(Items[freight_value]), Orders[is_delivered] = 1)','"BRL "#,0.00','Freight separately, delivered orders.'),
        'AOV BRL':('DIVIDE([Merchandise BRL], [Delivered Orders])','"BRL "#,0.00','Selected merchandise / distinct delivered orders in that scope.'),
        'Eligible Orders':(f'CALCULATE(DISTINCTCOUNT(Orders[order_id]), Orders[delivery_eligible] = 1, {scope})','#,0','Delivered orders with both actual and estimated dates.'),
        'Late Orders':(f'CALCULATE(DISTINCTCOUNT(Orders[order_id]), Orders[is_late] = 1, {scope})','#,0','Actual calendar date exceeds promised date.'),
        'Late Rate':('DIVIDE([Late Orders], [Eligible Orders])','0.00%','Late / delivery-eligible orders; eight missing dates excluded overall.'),
        'Mean Delivery Days':(f'CALCULATE(AVERAGE(Orders[delivery_days]), Orders[is_delivered] = 1, {scope})','0.00','Elapsed purchase-to-delivery days; negative/missing durations excluded.'),
        'Reviewed Orders':(f'CALCULATE(DISTINCTCOUNT(Orders[order_id]), Orders[is_delivered] = 1, Orders[review_eligible] = 1, {scope})','#,0','One latest selected valid review per delivered order.'),
        'Low Review Orders':(f'CALCULATE(DISTINCTCOUNT(Orders[order_id]), Orders[is_delivered] = 1, Orders[low_review] = 1, {scope})','#,0','Selected delivered-order reviews scored 1 or 2.'),
        'Low Review Rate':('DIVIDE([Low Review Orders], [Reviewed Orders])','0.00%','Low reviews / eligible reviewed delivered orders.'),
        'Mean Review':(f'CALCULATE(AVERAGE(Orders[review_score]), Orders[is_delivered] = 1, Orders[review_eligible] = 1, {scope})','0.00','Mean selected review among delivered orders.'),
        'Review Coverage':('DIVIDE([Reviewed Orders], [Delivered Orders])','0.00%','Reviewed delivered orders / delivered orders.'),
        'Qualified Late Rate':('IF([Eligible Orders] >= 100, [Late Rate])','0.00%','Suppressed below 100 eligible orders within current filters.'),
        'Qualified Eligible Orders':('IF([Eligible Orders] >= 100, [Eligible Orders])','#,0','Only groups with at least 100 eligible orders.'),
        'Qualified Late Orders':('IF([Eligible Orders] >= 100, [Late Orders])','#,0','Only groups with at least 100 eligible orders.'),
    }
    # A valid group with no late/low-review orders must display 0, while a
    # rate with no eligible denominator remains BLANK through DIVIDE.
    for n in ['Delivered Orders','Eligible Orders','Late Orders','Reviewed Orders','Low Review Orders']:
        expression,fmt,description=measures[n]
        measures[n]=(f'COALESCE({expression}, 0)',fmt,description)
    tables[0]['measures']=[{'name':n,'expression':v[0],'formatString':v[1],'description':v[2]} for n,v in measures.items()]
    relationships=[]
    for ft,fc,tt,tc in [('Items','order_id','Orders','order_id'),('Orders','purchase_date','Calendar','Date'),('Items','category_key','Categories','category_key'),('Items','seller_id','Sellers','seller_id')]:
        relationships.append({'name':str(uuid.uuid5(uuid.NAMESPACE_URL,ft+fc+tt+tc)),'fromTable':ft,'fromColumn':fc,'toTable':tt,'toColumn':tc,'fromCardinality':'many','toCardinality':'one','crossFilteringBehavior':'oneDirection'})
    write(model/'model.bim',{'name':'Olist','compatibilityLevel':1600,'model':{'culture':'en-US','defaultPowerBIDataSourceVersion':'powerBI_V3','tables':tables,'relationships':relationships,'annotations':[{'name':'PBI_QueryOrder','value':json.dumps(list(specs))}]}})
    (PBI/'measures.dax').write_text('\n\n'.join(f'-- {v[2]}\n{n} = {v[0]}' for n,v in measures.items()),encoding='utf8')
    definition=report/'definition'
    write(definition/'version.json',{'$schema':BASE+'report/definition/versionMetadata/1.0.0/schema.json','version':'1.0.0'})
    write(definition/'report.json',{'$schema':BASE+'report/definition/report/3.0.0/schema.json','themeCollection':{},'settings':{'defaultFilterActionIsDataFilter':True}})
    pages=['overview','delivery','experience']
    write(definition/'pages/pages.json',{'$schema':BASE+'report/definition/pagesMetadata/1.0.0/schema.json','pageOrder':pages,'activePageName':'overview'})
    counter=0
    def visual(page,typ,title,x,y,w,h,roles=None,sort=None,objects=None):
        nonlocal counter
        counter+=1; name=f'v{counter:03d}'
        config={'visualType':typ,'visualContainerObjects':{'title':[{'properties':{'show':literal(True),'text':literal(title),'fontSize':literal(12)}}]}}
        if roles:
            qs={}
            for role,fields in roles.items():
                qs[role]={'projections':[{'field':field(t,n,m),'queryRef':t+'.'+n,'nativeQueryRef':n} for t,n,m in fields]}
            config['query']={'queryState':qs}
            if sort:
                t,n,m,direction=sort
                config['query']['sortDefinition']={'sort':[{'field':field(t,n,m),'direction':direction}],'isDefaultSort':False}
        if objects:config['objects']=objects
        content={'$schema':BASE+'report/definition/visualContainer/2.0.0/schema.json','name':name,
            'position':{'x':x,'y':y,'z':counter,'height':h,'width':w,'tabOrder':counter},'visual':config}
        write(definition/f'pages/{page}/visuals/{name}/visual.json',content)
        return content
    def text(page,value,y,h=50):
        visual(page,'textbox','',24,y,1230,h,objects={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':value,'textStyle':{'fontSize':'12pt','fontFamily':'Segoe UI'}}]}]}}]})
    def chart(page,typ,title,x,y,w,h,cat,measure,sortmeasure=False):
        visual(page,typ,title,x,y,w,h,{'Category':[(cat[0],cat[1],False)],'Y':[('Orders',measure,True)]},
            ('Orders',measure,True,'Descending') if sortmeasure else (cat[0],cat[1],False,'Ascending'))
    for page,title in zip(pages,['Business overview','Delivery performance','Customer experience']):
        write(definition/f'pages/{page}/page.json',{'$schema':BASE+'report/definition/page/2.0.0/schema.json','name':page,'displayName':title,'displayOption':'FitToPage','height':820,'width':1280})
        text(page,title+' | Olist: historical Brazil, 2016–2018',12)
        for j,(t,n,label) in enumerate([('Calendar','Month','Purchase month'),('Categories','category_label','Product category')]):
            v=visual(page,'slicer',label,24+j*420,65,400,75,{'Values':[(t,n,False)]},objects={'data':[{'properties':{'mode':literal('Dropdown')}}]})
            v['visual']['syncGroup']={'groupName':label,'fieldChanges':True,'filterChanges':True}
            write(definition/f'pages/{page}/visuals/{v["name"]}/visual.json',v)
        if page=='overview':
            for j,m in enumerate(['Delivered Orders','Merchandise BRL','AOV BRL','Freight BRL']):visual(page,'card',m,24+j*310,155,294,110,{'Values':[('Orders',m,True)]})
            chart(page,'lineChart','Monthly delivered orders',24,285,605,330,('Calendar','Month'),'Delivered Orders')
            chart(page,'lineChart','Monthly merchandise value (BRL)',650,285,605,330,('Calendar','Month'),'Merchandise BRL')
            text(page,'Commercial scope: delivered orders. Merchandise excludes freight. AOV = selected merchandise / distinct delivered orders. Sparse 2016 and end-of-extract months are not comparable growth periods.',655,90)
        elif page=='delivery':
            for j,m in enumerate(['Eligible Orders','Late Orders','Late Rate','Mean Delivery Days']):visual(page,'card',m,24+j*310,155,294,110,{'Values':[('Orders',m,True)]})
            chart(page,'clusteredBarChart','Late-order volume by customer state',24,285,600,250,('Orders','customer_state'),'Late Orders',True)
            visual(page,'tableEx','Seller comparison: minimum 100 eligible orders',650,285,605,380,{'Values':[('Sellers','seller_label',False)]+[('Orders',m,True) for m in ['Qualified Eligible Orders','Qualified Late Orders','Qualified Late Rate']]},('Orders','Qualified Late Rate',True,'Descending'))
            chart(page,'lineChart','Late rate by purchase month',24,550,600,170,('Calendar','Month'),'Late Rate')
            text(page,'Late = actual delivery calendar date after promised date. Duration = elapsed purchase-to-delivery days. Seller outcome is whole-order association; overlapping seller counts are not additive.',745,65)
        else:
            for j,m in enumerate(['Reviewed Orders','Low Review Rate','Mean Review','Review Coverage']):visual(page,'card',m,24+j*310,155,294,110,{'Values':[('Orders',m,True)]})
            chart(page,'clusteredColumnChart','Review distribution: latest review per delivered order',24,285,600,230,('Orders','review_score'),'Reviewed Orders')
            chart(page,'clusteredColumnChart','Low-review rate by delivery outcome',650,285,605,230,('Orders','delivery_outcome'),'Low Review Rate')
            visual(page,'tableEx','Category priorities: volume and delay rate (minimum 100)',24,540,1230,180,{'Values':[('Categories','category_label',False)]+[('Orders',m,True) for m in ['Qualified Eligible Orders','Qualified Late Orders','Qualified Late Rate']]},('Orders','Qualified Late Orders',True,'Descending'))
            text(page,'Low review = score 1–2 among valid reviewed orders. Latest creation, answer timestamp, then review ID determines the selected review. Association does not establish causation; some reviews precede delivery.',745,65)
    # Validate all report JSON against downloaded Microsoft schemas without network.
    store={}
    for path in (PBI/'schemas').rglob('*.json'):
        schema=json.loads(path.read_text())
        key=BASE+path.relative_to(PBI/'schemas').as_posix()
        store[key]=schema
        if '$id' in schema:store[schema['$id']]=schema
    checked=0
    for path in list(report.rglob('*.json'))+[report/'definition.pbir',model/'definition.pbism']:
        content=json.loads(path.read_text());url=content.get('$schema')
        if url:
            schema=store[url]
            errors=list(Draft7Validator(schema,resolver=RefResolver(url,schema,store=store)).iter_errors(content))
            if errors:raise ValueError(str(path)+'\n'+'\n'.join(str(e) for e in errors[:3]))
            checked+=1
    write(PBI/'validation.json',{'microsoft_schema_validated_files':checked,'pages':3,'visuals':counter,'desktop_refresh_verified':False})
    print(f'Created PBIP: {checked} schema-valid files, 3 pages, {counter} visuals. Desktop QA pending.')

if __name__=='__main__': main()
