/* Readable saved evidence. No HTML from model output is ever executed. */
const CaseView = (() => {
  const {node} = UI;
  const label = text => String(text).replaceAll('_', ' ').replaceAll('-', ' ');
  const status = value => value === true || value === 'pass' ? 'pass' : value === false || value === 'fail' ? 'fail' : 'unknown';
  function verdict(value) {const state=status(value);return node('span', {pass:'✓ Passed',fail:'× Failed',unknown:'— Unscored'}[state], 'verdict '+state);}
  function prose(parent, text) {
    const box=node('div',undefined,'prose');let list=null,code=null;
    for(const line of String(text??'').split('\n')) {
      if(/^\s*```/.test(line)){if(code)code=null;else{list=null;code=node('pre');box.append(code);}continue;}if(code){code.append(document.createTextNode(line+'\n'));continue;}if(!line.trim())continue;const heading=line.match(/^(#{1,6})\s+(.*)/),bullet=line.match(/^\s*(?:([-*])|(\d+)[.)])\s+(.*)/),item=node(heading?'h4':bullet?'li':'p'),content=heading?heading[2]:bullet?bullet[3]:line;
      for(const part of content.split(/(\*\*[^*]+\*\*|`[^`]+`)/g))item.append(part.startsWith('**')?node('strong',part.slice(2,-2)):part.startsWith('`')&&part.endsWith('`')&&part.length>1?node('code',part.slice(1,-1)):document.createTextNode(part));
      if(bullet){const kind=bullet[1]?'UL':'OL';if(list?.tagName!==kind){list=node(kind.toLowerCase());if(bullet[2])list.start=Number(bullet[2]);box.append(list);}list.append(item);}else{list=null;box.append(item);}
    }
    parent.append(box);
  }
  function decoded(data) {
    if(typeof data==='string'){const text=data.trim().replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/i,'$1');if(/^[\[{]/.test(text)){try{return JSON.parse(text);}catch{ /* Keep malformed JSON readable as text. */ }}}return data;
  }
  function value(parent, data) {
    data=decoded(data);
    if(data===null||data===undefined){parent.append(node('span',data===null?'null':'Not recorded','muted'));return;}
    if(typeof data==='string'){const box=node('div'),button=node('button','Read full text','text-toggle'),long=data.length>400;let expanded=!long;parent.append(box);if(long)parent.append(button);function paint(){box.replaceChildren();prose(box,data===''?'""':expanded?data:data.slice(0,400)+'…');button.textContent=expanded?'Show less':'Read full text';button.setAttribute('aria-expanded',String(expanded));}button.onclick=()=>{expanded=!expanded;paint();};paint();return;}
    if(typeof data!=='object'){parent.append(node('span',String(data)));return;}
    const entries=Object.entries(data);if(!entries.length){parent.append(node('span',Array.isArray(data)?'[]':'{}','muted'));return;}let offset=0;
    const body=node('div',undefined,'data-fields'),more=node('button',undefined,'text-toggle');parent.append(body);
    function paint(){for(const [key,raw] of entries.slice(offset,offset+8)){const item=decoded(raw),row=node('div',undefined,'data-field'),cell=node('div',undefined,'data-value'),name=Array.isArray(data)?`${Number(key)+1} · ${[item?.title,item?.name,item?.id].find(v=>['string','number'].includes(typeof v)&&String(v).length)??'Item'}`:key,nested=item!==null&&typeof item==='object',size=nested?Object.keys(item).length:0;if(typeof item==='string'&&item.length>80)row.classList.add('data-long');if(size){const button=node('button',undefined,'data-branch');button.append(node('span',name,'field-label'),node('span',`${size} ${Array.isArray(item)?'item':'field'}${size===1?'':'s'}`,'small'));button.setAttribute('aria-expanded','false');cell.hidden=true;button.onclick=()=>{cell.hidden=!cell.hidden;button.setAttribute('aria-expanded',String(!cell.hidden));if(!cell.childNodes.length)value(cell,item);};row.append(button);}else{row.append(node('div',name,'field-label'));value(cell,item);}row.append(cell);body.append(row);}offset+=8;more.remove();if(offset<entries.length){more.textContent=`Show next ${Math.min(8,entries.length-offset)} · ${entries.length-offset} remaining`;parent.append(more);}}
    more.onclick=paint;paint();
  }
  function section(parent, title, content) {parent.append(node('h3',title));value(parent,content);}
  function messages(row) {
    const seen=new Set(), result=[];
    for(const group of row.model_roles||[])for(const message of group.messages||[]){const key=JSON.stringify([group.role,message]);if(seen.has(key))continue;seen.add(key);result.push({...message,role:group.role});}
    return result.sort((a,b)=>String(a.timestamp||'').localeCompare(String(b.timestamp||'')));
  }
  function request(row) {
    const input=row.input;
    if(typeof input==='string')return input;
    for(const key of ['question','request','objective','message','prompt'])if(typeof input?.[key]==='string')return input[key];
    return messages(row).filter(m=>m.role==='subject').flatMap(m=>m.parts||[]).find(p=>p.part_kind==='user-prompt'&&typeof p.content==='string')?.content||'No request was recorded.';
  }
  function answer(parent,row) {
    if(row.error)parent.append(node('p',row.error,'warning'));
    prose(parent,row.answer||'No answer was saved for this attempt.');
    if(row.public_rationale)section(parent,'Agent explanation',row.public_rationale);
    if(row.agent_disposition&&row.agent_disposition!=='completed')parent.append(node('p',label(row.agent_disposition),'muted'));
  }
  function evaluation(parent,row) {
    if(row.verifier?.status!=='available')parent.append(node('p',row.verifier?.reason||'No independent evaluation was recorded.','warning'));
    if(row.verifier?.error||row.judge_error)section(parent,'Evaluation error',row.verifier?.error||row.judge_error);
    for(const [title,checks] of [['Independent checks',row.verifier?.checks],['Flags',row.verifier?.red_flags],['Judge',row.judge]]) {
      if(title==='Judge'&&!checks?.length){parent.append(node('h3','Judge'),node('p',row.judge_summary||'No judge evaluation was recorded.','muted'));continue;}
      if(!checks?.length)continue;
      parent.append(node('h3',title));
      if(title==='Judge'&&row.judge_summary)value(parent,row.judge_summary);
      for(const check of checks){const item=node('article',undefined,'check'),head=node('button',undefined,'check-heading'),body=node('div');head.append(title==='Flags'?node('span','! Flag','verdict fail'):verdict((title==='Independent checks'&&row.verifier?.status!=='available')||(title==='Judge'&&row.judge_status!=='available')?null:check.status??check.decision),node('strong',check.label||label(check.id||check.criterion||'Review')));item.append(head,body);if(check.reason||check.summary)value(body,check.reason||check.summary);const extra=Object.fromEntries(Object.entries(check).filter(([key])=>!['id','label','criterion','status','decision','reason','summary','dimension','version'].includes(key)));if(Object.keys(extra).length)value(body,extra);if(!body.childNodes.length){const plain=node('div',undefined,'check-heading');plain.append(...head.childNodes);head.replaceWith(plain);parent.append(item);continue;}body.hidden=head.firstChild.classList.contains('pass');head.setAttribute('aria-expanded',String(!body.hidden));head.onclick=()=>{body.hidden=!body.hidden;head.setAttribute('aria-expanded',String(!body.hidden));};parent.append(item);}
    }
    for(const [title,items] of [['Metrics',row.verifier?.metrics],['Assessments',row.assessments]])if(items&&Object.keys(items).length)section(parent,title,items);
  }
  function trace(parent,row) {
    const recorded=messages(row),returns=new Map(),events=[...(row.tool_events||[])],used=new Set();
    function canonical(value){if(typeof value==='string'){try{return canonical(JSON.parse(value));}catch{return value;}}return JSON.stringify(value,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.entries(v).sort(([a],[b])=>a.localeCompare(b))):v);}
    for(const message of recorded)for(const part of message.parts||[])if(part.part_kind==='tool-return')returns.set(part.tool_call_id,part);
    const steps=[];
    for(const message of recorded)for(const part of message.parts||[]) {
      const kind=part.part_kind;
      if(['tool-return','system-prompt'].includes(kind))continue;
      const event=kind==='tool-call'?events.find(e=>!used.has(e)&&(!e.role||e.role===message.role)&&e.tool===part.tool_name&&(canonical(e.arguments)===canonical(part.args)||(returns.has(part.tool_call_id)&&canonical(e.result)===canonical(returns.get(part.tool_call_id).content)&&Date.parse(e.started_at)>=Date.parse(message.timestamp)&&Date.parse(e.started_at)<=Date.parse(returns.get(part.tool_call_id).timestamp)&&Object.entries(decoded(part.args)||{}).every(([key,v])=>canonical(v)===canonical(decoded(e.arguments)?.[key]))))):null;if(event)used.add(event);
      steps.push({title:kind==='tool-call'?part.tool_name:kind==='user-prompt'?'Incoming message':kind==='thinking'?'Reasoning':'Response',role:message.role,kind,content:kind==='tool-call'?(event?.arguments??part.args):part.content,result:returns.has(part.tool_call_id)?returns.get(part.tool_call_id).content:event?.result,error:event?.error,status:event?.status,time:message.timestamp});
    }
    for(const event of events)if(!used.has(event))steps.push({title:event.tool,role:event.role||'subject',kind:'tool-call',content:event.arguments,result:event.result,error:event.error,status:event.status,time:event.started_at});
    steps.sort((a,b)=>(Date.parse(a.time)||0)-(Date.parse(b.time)||0));
    if(!steps.length){parent.append(node('p','No steps were recorded.','empty'));return;}
    parent.append(node('p',`${steps.length} recorded steps`,'muted'));
    for(const [i,step] of steps.entries()) {
      const item=node('article',undefined,'trace-step'),button=node('button',undefined,'trace-button'),body=node('div',undefined,'trace-content');body.hidden=true;
      button.append(node('span',String(i+1),'step-number'),node('strong',step.title),node('span',step.status==='error'?'× Error':step.status==='unconfirmed'?'? Unconfirmed':'',step.status==='error'?'fail':'unknown'),node('span',step.role&&step.role!=='subject'?label(step.role):'','muted'));button.setAttribute('aria-expanded','false');
      button.onclick=()=>{body.hidden=!body.hidden;button.setAttribute('aria-expanded',String(!body.hidden));if(!body.childNodes.length){if(step.kind==='tool-call'){if(step.content&&Object.keys(decoded(step.content)).length)section(body,'Arguments',step.content);}else value(body,step.content);if(step.result!==undefined)section(body,'Result',step.result);if(step.error)section(body,'Error',step.error);}};
      item.append(button,body);parent.append(item);
    }
  }
  function inputs(parent,row) {
    section(parent,'Request',request(row));
    if(row.input!==undefined&&row.input!==request(row))section(parent,'Provided context',row.input);
    if(row.sources?.length)section(parent,'Sources',row.sources);
    if(Object.keys(row.state_snapshots||{}).length)section(parent,'State snapshots',row.state_snapshots);
  }
  function render(parent,entries,view='Answer',selection=new Map()) {
    const grid=node('div',undefined,'comparison-grid');
    for(const [role,record] of entries) {
      const side=node('section',undefined,'comparison-side'),header=node('div',undefined,'side-heading'),body=node('div',undefined,'side-body');
      header.append(node('h3',role));
      const attempts=[record.raw_capture,...(record.raw_capture.previous_attempts||[])];let selected=selection.get(record.id)||0;
      const statusLine=node('div',undefined,'side-status');header.append(statusLine);
      if(attempts.length>1){const select=node('select');select.setAttribute('aria-label',role+' attempt');attempts.forEach((a,i)=>{const option=node('option',i===0?'Latest attempt':`Earlier attempt ${i} · ${label(a.execution_status)}`);option.value=i;select.append(option);});select.value=String(selected);select.onchange=()=>{selected=Number(select.value);selection.set(record.id,selected);paint()};header.append(select);}
      function paint(){const row=attempts[selected];statusLine.replaceChildren(verdict(row.verifier?.status==='available'?row.verifier.goal_pass:null));if(row.execution_status!=='completed')statusLine.append(node('span',label(row.execution_status),'warning-inline'));body.replaceChildren();if(selected)body.append(node('p','Earlier attempt · the case comparison uses the latest attempt.','warning'));({Answer:answer,Evaluation:evaluation,Steps:trace,Input:inputs})[view](body,row);if(view==='Evaluation'){const usage=node('dl',undefined,'case-usage');for(const [key,val] of [['Cost',UI.money(row.metrics?.cost_usd)],['Time',UI.duration(row.metrics?.latency_ms)],['Input tokens',UI.number(row.usage?.input_tokens)],['Output tokens',UI.number(row.usage?.output_tokens)]])usage.append(node('dt',key),node('dd',val));body.append(usage);}}
      side.append(header,body);grid.append(side);paint();
    }
    parent.append(grid);
  }
  return {render,request,verdict,value,prose};
})();
