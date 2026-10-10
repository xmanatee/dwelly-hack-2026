async function showReport(){
const packed=JSON.parse(document.getElementById('report-data').textContent);
const report=packed.encoding==='gzip-base64' ? JSON.parse(await new Response(new Blob([Uint8Array.from(atob(packed.data),c=>c.charCodeAt(0))]).stream().pipeThrough(new DecompressionStream('gzip'))).text()) : packed;
const {node,pretty,short}=UI;
document.title=report.title+' · dwelly';document.getElementById('title').textContent=report.title;document.getElementById('subtitle').textContent=report.subtitle;
document.getElementById('download').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(report)],{type:'application/json'})),link=node('a');link.href=url;link.download='report.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
if(report.receipt.runs?.length&&!report.receipt.analysis_only&&!report.receipt.source_analyses){showExperiment(report);return;}

const collator=new Intl.Collator('en-GB',{numeric:true});
const dialog=document.getElementById('drawer');
document.getElementById('close').onclick=()=>dialog.close();
dialog.onclick=event=>{if(event.target===dialog&&event.clientX<dialog.getBoundingClientRect().left)dialog.close()};
function detail(box,row){box.append(node('h2',row.title||row.id||row.record_id||'Record'));if(row.fields)CaseView.value(box,row.fields);if(row.sample_rows){box.append(node('h3','Sample records'));table(box,{rows:row.sample_rows,total:row.fields?.['Source rows']})}
 if(row.insights){box.append(node('p',row.insights.summary));for(const name of ['goals','facts','reported_actions','conversation_functions','exception_candidates']){const claims=row.insights[name]||[];if(!claims.length)continue;box.append(node('h3',name.replaceAll('_',' ')));const list=node('ul',undefined,'claims');for(const c of claims){const li=node('li',c.text);li.append(node('span',' · '+c.support,'small'));for(const cite of c.evidence||[])li.append(node('span',`${cite.source_id}: “${cite.quote}”`,'cite'));list.append(li)}box.append(list)}if(row.insights.missing_information?.length){box.append(node('h3','Missing information'),node('p',row.insights.missing_information.join(' · ')))}}
 if(row.summary&&!row.insights)box.append(node('p',row.summary));
 if(row.findings?.length){box.append(node('h3','Findings'));for(const finding of row.findings){const item=node('div',undefined,'record');item.append(node('strong',finding.description),node('span',finding.category.replaceAll('_',' '),'tag'));if(finding.scope)item.append(node('span',finding.scope.replaceAll('_',' '),'small'));for(const cite of finding.evidence||[])item.append(node('span',`${cite.source_id}: “${cite.quote}”`,'cite'));if(finding.next_check)item.append(node('p',finding.next_check));box.append(item)}}
 if(row.sampling_reasons?.length)box.append(node('p',row.sampling_reasons.join(' · '),'small'));
 if(row.audit){box.append(node('h3','Review'),node('p',row.audit.decision+' · '+row.audit.reason));}
 for(const s of row.sources||[]){box.append(node('h3',s.id||s.source||'Source'));CaseView.value(box,s.text||s)}
 if(row.text){box.append(node('h3','Source text'));CaseView.value(box,row.text);}
 if(!row.fields&&!row.insights&&!row.text&&!row.sources)CaseView.value(box,Object.fromEntries(Object.entries(row).filter(([key])=>!['title','id'].includes(key))));
 if(row.extraction_error)box.append(node('h3','Extraction failed'),node('p',row.extraction_error));
 if(row.analysis_trace){box.append(node('h3','Model analysis'));box.append(node('p',row.analysis_trace.reused?'Reused saved analysis · 0 new requests':`${row.analysis_trace.new_requests||0} model requests`));CaseView.value(box,row.analysis_trace)}
}
function inspect(record){const box=document.getElementById('detail');box.replaceChildren();if(record.comparison){const rows=report.blocks.filter(b=>b.kind==='records').flatMap(b=>b.data.rows||[]);CaseView.render(box,Object.entries(record.comparison).map(([role,id])=>[role==='baseline'?'Baseline':'Experiment',rows.find(r=>r.id===id)]));}else if(record.raw_capture)CaseView.render(box,[['Run',record]]);else detail(box,record);dialog.showModal();}

function table(section,data){const rows=data.rows||[];const cols=[...new Set(rows.flatMap(r=>Object.keys(r)))];const controls=node('div',undefined,'controls');const filter=node('input');filter.placeholder='Search displayed rows';filter.setAttribute('aria-label','Search displayed rows');const count=node('span',undefined,'small');const prev=node('button','Previous'),next=node('button','Next');controls.append(filter,prev,next,count);if(rows.length>DISPLAY.page_size)section.append(controls);const wrap=node('div',undefined,'table-wrap');const t=node('table'),head=node('thead'),body=node('tbody');let page=0,sortKey=null,ascending=true;const size=DISPLAY.page_size;const hr=node('tr');for(const col of cols){const th=node('th');const b=node('button',col.replaceAll('_',' '));b.onclick=()=>{ascending=sortKey===col?!ascending:true;sortKey=col;for(const cell of hr.children)cell.removeAttribute('aria-sort');th.setAttribute('aria-sort',ascending?'ascending':'descending');page=0;paint()};th.append(b);hr.append(th)}head.append(hr);t.append(head,body);wrap.append(t);section.append(wrap);
 function paint(){let visible=rows.filter(r=>pretty(r).toLowerCase().includes(filter.value.toLowerCase()));if(sortKey)visible.sort((a,b)=>{const x=a[sortKey],y=b[sortKey];return (typeof x==='number'&&typeof y==='number'?x-y:collator.compare(String(x??''),String(y??'')))*(ascending?1:-1)});page=Math.min(page,Math.max(0,Math.ceil(visible.length/size)-1));body.replaceChildren();for(const r of visible.slice(page*size,page*size+size)){const tr=node('tr');tr.tabIndex=0;tr.onclick=()=>inspect(r);tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect(r)}};for(const col of cols)tr.append(node('td',short(r[col])));body.append(tr)}if(!visible.length){const empty=node('td','No matching records.','empty');empty.colSpan=cols.length||1;const tr=node('tr');tr.append(empty);body.append(tr);}count.textContent=`${visible.length} displayed${data.total!==null&&data.total!==undefined?' / '+data.total+' source rows':''} · page ${visible.length?page+1:0}`;prev.disabled=page===0;next.disabled=(page+1)*size>=visible.length}
 filter.oninput=()=>{page=0;paint()};prev.onclick=()=>{page--;paint()};next.onclick=()=>{page++;paint()};paint();}
function records(section,rows){
 const search=node('input');search.type='search';search.placeholder='Search records';search.setAttribute('aria-label','Search records');const list=node('div',undefined,'records-list'),more=node('button','Show more');let limit=24;
 function paint(){list.replaceChildren();const selected=rows.filter(r=>JSON.stringify(r).toLowerCase().includes(search.value.toLowerCase()));for(const row of selected.slice(0,limit)){const card=node('button',undefined,'record record-button');card.append(node('strong',row.title&&rows.some(other=>other!==row&&other.title===row.title)?row.id||row.record_id||row.title:row.title||row.id||row.record_id||'Record'));if(row.summary||row.insights?.summary)card.append(node('p',short(row.summary||row.insights.summary)));card.onclick=()=>inspect(row);list.append(card);}more.hidden=selected.length<=limit;if(!selected.length)list.append(node('p','No matching records.','empty'));}
 search.oninput=()=>{limit=24;paint()};more.onclick=()=>{limit+=24;paint()};if(rows.length>DISPLAY.page_size)section.append(search);section.append(list,more);paint();
}
const groups=[...new Set(report.blocks.map(b=>b.section).filter(Boolean))],nav=document.getElementById('nav'),panels=new Map();
if(groups.length){nav.setAttribute('aria-label','Dataset views');groups.forEach((group,index)=>{const panel=node('div',undefined,'analysis-section');panel.id='section-panel-'+index;panel.setAttribute('role','tabpanel');panel.tabIndex=0;document.getElementById('blocks').append(panel);panels.set(group,panel);});let initializing=true;const choose=UI.tabs(nav,groups,new URLSearchParams(location.hash.slice(1)).get('section'),(group,button)=>{const panel=panels.get(group);button.setAttribute('aria-controls',panel.id);panel.setAttribute('aria-labelledby',button.id);for(const [name,p] of panels)p.hidden=name!==group;requestAnimationFrame(()=>panel.querySelectorAll('.js-plotly-plot').forEach(chart=>Plotly.Plots.resize(chart)));if(!initializing){const hash='#section='+encodeURIComponent(group);if(location.hash!==hash)history.pushState(null,'',hash);}});initializing=false;window.addEventListener('popstate',()=>{initializing=true;choose(new URLSearchParams(location.hash.slice(1)).get('section'));initializing=false;});}
const visible=report.blocks.filter(b=>!b.collapsed);let halfOpen=false;const overview=report.blocks.find(b=>b.kind==='metrics'&&!b.collapsed);
document.getElementById('report-kind').textContent=report.receipt.analysis_only?'Data analysis':report.receipt.comparisons?.length?'Experiment':'Run report';
report.blocks.forEach((b,index)=>{
 let width=b.width;if(!b.collapsed){const next=visible[visible.indexOf(b)+1];if(width==='half'){if(!halfOpen&&next?.width!=='half')width='full';else halfOpen=!halfOpen;}else halfOpen=false;}
 const section=node('section',undefined,'panel '+width);section.id='block-'+index;
 let content=section;
 const heading=node('div',undefined,'section-head');heading.append(node('h2',b.title));section.append(heading);const link=node('a',b.title);link.href='#'+section.id;if(!groups.length&&b.kind!=='metrics')nav.append(link);
 if(b.note)content.append(node('p',b.note,'caption'));
 if(b.caption)content.append(node('p',b.caption,'caption'));
 (b===overview?document.getElementById('overview'):panels.get(b.section)||document.getElementById('blocks')).append(section);
 if(b.kind==='text')CaseView.prose(content,b.data.text);
 if(b.kind==='metrics'){section.classList.add('overview');const grid=node('div',undefined,'metrics');for(const [k,v] of Object.entries(b.data)){const m=node('div',undefined,'metric');m.append(node('b',UI.pretty(v)),node('span',k));grid.append(m)}content.append(grid)}
 if(b.kind==='table')table(content,b.data);
 if(b.kind==='chart'){
  const chart=node('div',undefined,'chart');content.append(chart);
  const plotted=Plotly.newPlot(chart,UI.chartText(b.data.data||[]),UI.chartText(b.data.layout||{}),{responsive:true,displaylogo:false,displayModeBar:false});
  Promise.resolve(plotted).catch(error=>{chart.replaceChildren(node('p','Chart failed: '+error.message,'badge fail'));throw error;}).then(()=>{if(chart.on&&Object.keys(b.data.details||{}).length)chart.on('plotly_click',event=>{const id=event.points?.[0]?.customdata;const key=Object.keys(b.data.details).find(key=>UI.chartText(key)===(Array.isArray(id)?id[0]:id));const record=b.data.details[key];if(record)inspect(record)})});
 }
 if(b.kind==='records')records(content,b.data.rows||[]);
 if(b.kind==='flow'){const flow=node('div',undefined,'flow');for(const [i,s] of (b.data.steps||[]).entries()){const step=node('div',undefined,'step');step.append(node('strong',`${i+1}. ${s.action||s.title||'Step'}`));if(s.condition)step.append(node('p',s.condition));if(s.tool)step.append(node('span',s.tool,'small'));flow.append(step)}content.append(flow)}
});
const sectionObserver=new IntersectionObserver(entries=>{for(const entry of entries)if(entry.isIntersecting){for(const link of document.querySelectorAll('#nav a'))link.setAttribute('aria-current',String(link.hash==='#'+entry.target.id));}},{rootMargin:'-15% 0px -65% 0px'});
if(!groups.length)for(const section of document.querySelectorAll('#blocks > section'))sectionObserver.observe(section);

}
showReport().catch(error=>{document.getElementById('title').textContent='Report could not load';document.getElementById('subtitle').textContent=error.message+' · Open this file in a current browser.';});
