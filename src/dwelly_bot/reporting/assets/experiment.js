/* One case index, with stable baseline / experiment columns at every depth. */
function showExperiment(report) {
  const {node}=UI, blocks=report.blocks, pair=report.receipt.comparisons?.[0];
  document.getElementById('subtitle').textContent=report.receipt.experiment?.description||report.subtitle;
  document.body.classList.add('experiment');document.getElementById('report-kind').textContent=pair?'Comparison':'Run';
  const runs=pair?[pair.baseline,pair.candidate].map(id=>report.receipt.runs.find(r=>r.id===id)):report.receipt.runs;
  const captures=blocks.filter(b=>b.kind==='records').flatMap(b=>b.data.rows||[]).filter(r=>r.raw_capture),saved=new Map(captures.map(r=>[r.id,r]));
  const changes=blocks.find(b=>b.title==='Case comparison')?.data.rows||captures;
  const model=run=>run.manifest.model||run.id,role=i=>pair?(i===0?'Baseline':'Experiment'):'Run';
  const resourceRows=blocks.find(b=>b.title==='Run resources')?.data.rows||[];
  const summaries=node('div',undefined,'run-summaries');
  for(const [i,run] of runs.entries()) {
    const rows=captures.filter(r=>r.run_id===run.id),counts={pass:0,fail:0,unknown:0};rows.forEach(r=>counts[r.goal_status]++);
    const card=node('section',undefined,'run-summary'),head=node('div',undefined,'summary-heading');
    head.append(node('span',role(i),'eyebrow'),node('strong',model(run)),node('span',counts.unknown===rows.length?'Correctness unknown':`${counts.pass} / ${rows.length} passed`,'score'));card.append(head);
    const bar=node('div',undefined,'outcome-bar');bar.setAttribute('role','img');bar.setAttribute('aria-label',`${counts.pass} passed, ${counts.fail} failed, ${counts.unknown} unscored`);
    for(const [state,n] of Object.entries(counts)){const part=node('span',undefined,state);part.style.width=`${rows.length?100*n/rows.length:0}%`;bar.append(part);}
    const legend=node('div',undefined,'outcome-legend');for(const [state,text] of [['pass','Passed'],['fail','Failed'],['unknown','Unscored']])legend.append(node('span',state==='pass'?text:`${text} ${counts[state]}`,state));card.append(bar,legend);
    const stats=resourceRows.find(r=>r.Role===(i===0?'baseline':'candidate'))||resourceRows[i]||{};
    const execution=node('p',`${rows.filter(r=>r.raw_capture.execution_status==='completed').length} / ${rows.length} cases executed · ${counts.unknown} outcomes unscored`,'small');card.append(execution);
    const resources=node('div',undefined,'run-stats'),attempts=rows.flatMap(r=>[r.raw_capture,...(r.raw_capture.previous_attempts||[])]);
    function tokens(key,total){const known=attempts.map(a=>a.usage?.[key]).filter(Number.isFinite);return total!=null?UI.number(total):known.length?'≥ '+UI.number(known.reduce((a,b)=>a+b,0)):'—';}
    const cost=stats['Execution cost (USD)'],knownCost=stats['Known cost (USD)'];
    for(const [label,text] of [[cost==null?'Known cost':'Cost',cost==null&&knownCost!=null?'≥ '+UI.money(knownCost):UI.money(cost)],['Input tokens',tokens('input_tokens',stats['Input tokens'])],['Output tokens',tokens('output_tokens',stats['Output tokens'])],['Mean / attempt',stats['Mean case time (s)']==null?'—':UI.duration(stats['Mean case time (s)']*1000)]]){const cell=node('div');cell.append(node('span',label,'small'),node('strong',text));resources.append(cell);}card.append(resources);summaries.append(card);
  }
  document.getElementById('overview').append(summaries);
  const workspace=node('section',undefined,'workspace'),sidebar=node('aside',undefined,'case-index'),detail=node('section',undefined,'case-detail');sidebar.setAttribute('aria-label','Cases');detail.setAttribute('aria-label','Selected case');workspace.append(sidebar,detail);document.getElementById('blocks').append(workspace);
  const notes=node('footer',undefined,'run-notes');notes.append(node('h2','Run details'));const configGrid=node('div',undefined,'comparison-grid');runs.forEach((run,i)=>{const column=node('section');column.append(node('h3',role(i)));const config=run.manifest.resolved_config||{};CaseView.value(column,{'Model':run.manifest.model,'Dataset':run.manifest.dataset,'Parallel cases':config.case_concurrency,'Source revision':run.manifest.code_revision});configGrid.append(column);});notes.append(configGrid);const limitations=[...new Set(captures.flatMap(r=>r.raw_capture.verifier?.limitations||[]))];if(limitations.length){notes.append(node('h3','Evaluation scope'));const list=node('ul');limitations.forEach(text=>list.append(node('li',text)));notes.append(list);}notes.append(node('p','≥ marks partial totals. Usage includes earlier attempts. Mean time is per measured attempt; concurrency and provider latency affect it.'));if(report.receipt.attribution)notes.append(node('p',report.receipt.attribution));workspace.after(notes);
  const indexHead=node('div',undefined,'index-head'),search=node('input');search.type='search';search.placeholder='Search cases or answers';search.setAttribute('aria-label','Search cases or answers');indexHead.append(node('h2','Cases'),search);
  const pager=node('div',undefined,'case-pagination'),older=node('button','Previous'),newer=node('button','Next');older.setAttribute('aria-label','Previous cases page');newer.setAttribute('aria-label','Next cases page');pager.append(older,newer);let page=0;const pageSize=12;
  const filter=node('div',undefined,'case-filters'),list=node('div',undefined,'case-list'),count=node('div',undefined,'case-count');count.setAttribute('aria-live','polite');sidebar.append(indexHead,filter,count,list,pager);
  const changeNames={regressed:'↓ Regression',improved:'↑ Improvement',unknown:'Unscored','not comparable':'Not comparable',unchanged:'Same outcome'};
  const names={all:'All',pass:'✓ Passed',fail:'× Failed',regressed:'↓ Regressions',improved:'↑ Improvements',different:'≠ Answers differ',unknown:'Unscored','not comparable':'Not comparable',unchanged:'Unchanged'};
  const rows=changes.map(row=>{const records=row.comparison?[saved.get(row.comparison.baseline),saved.get(row.comparison.candidate)]:[row];const request=CaseView.request(records[0].raw_capture);return {row,records,id:String(row.fields?.Case||row.raw_capture.id),request,different:pair&&(records[0].raw_capture.answer??'')!==(records[1].raw_capture.answer??''),text:JSON.stringify([row.fields?.Case,request,...records.map(r=>[r.raw_capture.answer,r.raw_capture.public_rationale])]).toLowerCase()};});
  const ranks={regressed:0,improved:1,'not comparable':2,unknown:3,unchanged:4};rows.sort((a,b)=>(ranks[a.row.change]??5)-(ranks[b.row.change]??5)||a.id.localeCompare(b.id,'en',{numeric:true}));
  const views=['Answer','Evaluation','Steps','Input'];const attemptSelection=new Map();let active=rows.find(r=>r.id===new URLSearchParams(location.hash.slice(1)).get('case'))||null,currentFilter='all',currentView=views.find(v=>v.toLowerCase()===new URLSearchParams(location.hash.slice(1)).get('view'))||'Answer',visible=rows;
  const buttons=new Map();
  const matches=(r,key)=>key==='all'||(key==='different'?r.different:!pair?r.records[0].goal_status===key:r.row.change===key);
  for(const key of pair?['all','regressed','improved','different','unknown','not comparable']:['all','fail','pass','unknown']) {
    const total=rows.filter(r=>matches(r,key)).length;if(key!=='all'&&!total)continue;
    const button=node('button',`${names[key]} ${total}`);button.onclick=()=>{currentFilter=key;page=0;active=null;paintList()};buttons.set(key,button);filter.append(button);
  }
  function saveLocation(replace=false){const hash='#case='+encodeURIComponent(active.id)+(currentView==='Answer'?'':'&view='+currentView.toLowerCase());if(location.hash!==hash)history[replace?'replaceState':'pushState'](null,'',hash);}
  function select(item,updateURL=true){active=item;const targetPage=Math.floor(visible.indexOf(item)/pageSize);if(targetPage!==page){page=targetPage;paintList();}else{for(const button of list.children)button.setAttribute('aria-current',String(button.dataset.case===item.id));paintDetail();}if(updateURL){saveLocation();detail.scrollIntoView({block:'start'});}}
  function paintList() {
    visible=rows.filter(r=>matches(r,currentFilter)&&r.text.includes(search.value.toLowerCase()));buttons.forEach((b,key)=>b.setAttribute('aria-pressed',String(key===currentFilter)));page=Math.max(0,Math.min(page,Math.ceil(visible.length/pageSize)-1));count.textContent=visible.length?`${page*pageSize+1}–${Math.min((page+1)*pageSize,visible.length)} of ${visible.length} cases`:'0 cases';older.disabled=page===0;newer.disabled=(page+1)*pageSize>=visible.length;pager.hidden=visible.length<=pageSize;list.replaceChildren();
    for(const item of visible.slice(page*pageSize,(page+1)*pageSize)){const button=node('button',undefined,'case-row');button.dataset.case=item.id;button.setAttribute('aria-current',String(active===item));button.append(node('strong',item.id));const outcomes=node('span',undefined,'row-outcomes');for(const [i,record] of item.records.entries())outcomes.append(node('span',`${pair?(i===0?'B':'E')+' ':''}${{pass:'✓',fail:'×',unknown:'—'}[record.goal_status]}`,record.goal_status));outcomes.setAttribute('aria-label',item.records.map((r,i)=>`${role(i)} ${r.goal_status}`).join(', '));button.append(outcomes);button.onclick=()=>select(item);list.append(button);}
    if(!visible.length){list.append(node('p','No matching cases.','empty'));detail.replaceChildren(node('p','Change the filter or search to see cases.','empty'));active=null;}else if(!visible.includes(active)){active=visible[page*pageSize];paintList();saveLocation(true);}else paintDetail();
  }
  function paintDetail() {
    detail.replaceChildren();const title=node('div',undefined,'detail-title'),previous=node('button','←'),next=node('button','→'),index=visible.indexOf(active);previous.setAttribute('aria-label','Previous case');next.setAttribute('aria-label','Next case');previous.disabled=index<=0;next.disabled=index===visible.length-1;previous.onclick=()=>select(visible[index-1]);next.onclick=()=>select(visible[index+1]);title.append(node('h2',active.id),node('span',pair?(changeNames[active.row.change]||active.row.change):'','change '+(active.row.change||'')),previous,next);detail.append(title);
    const request=node('div',undefined,'case-request');request.append(node('span',pair&&CaseView.request(active.records[1].raw_capture)!==active.request?'Baseline opening message · compare both in Input':'Request','eyebrow'));CaseView.prose(request,active.request);detail.append(request);
    if(active.row.change==='not comparable')detail.append(node('p',active.row.fields.Reason,'warning'));
    const tabs=node('div',undefined,'case-tabs'),body=node('div',undefined,'case-panels');tabs.id='case-tabs';tabs.setAttribute('aria-label','Case view');body.id='case-panel';body.setAttribute('role','tabpanel');detail.append(tabs,body);
    let initializing=true;UI.tabs(tabs,views,currentView,(view,button)=>{currentView=view;button.setAttribute('aria-controls',body.id);body.setAttribute('aria-labelledby',button.id);body.replaceChildren();CaseView.render(body,active.records.map((r,i)=>[role(i),r]),view,attemptSelection);if(!initializing)saveLocation();});initializing=false;
  }
  function fromURL(){const params=new URLSearchParams(location.hash.slice(1));currentView=views.find(v=>v.toLowerCase()===params.get('view'))||'Answer';const id=params.get('case'),item=rows.find(r=>r.id===id);if(item){currentFilter='all';search.value='';active=item;visible=rows;page=Math.floor(rows.indexOf(item)/pageSize);paintList();}}
  older.onclick=()=>{page--;paintList();};newer.onclick=()=>{page++;paintList();};search.oninput=()=>{page=0;paintList();};window.addEventListener('popstate',fromURL);if(active)page=Math.floor(rows.indexOf(active)/pageSize);paintList();
}
