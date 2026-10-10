const UI = {
  node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=String(text);if(cls)e.className=cls;return e;},
  number(value){
    if(!Number.isFinite(value))return '—';
    const options = value !== 0 && Math.abs(value) < 10 ** -DISPLAY.decimals
      ? {maximumSignificantDigits:DISPLAY.small_digits} : {maximumFractionDigits:DISPLAY.decimals};
    return value.toLocaleString('en-GB', options);
  },
  money(value){return value == null ? 'Not recorded' : '$' + UI.number(value);},
  duration(ms){if(ms==null)return 'Not recorded';const seconds=Math.round(ms/1000);return seconds>=60?`${Math.floor(seconds/60)}m ${seconds%60}s`:UI.number(ms/1000)+' s';},
  pretty(value){return typeof value==='number'?UI.number(value):typeof value==='object'&&value!==null?JSON.stringify(value,null,2):String(value??'—');},
  short(value){if(Array.isArray(value))return `${value.length} items ↗`;if(value&&typeof value==='object')return 'Details ↗';const text=UI.pretty(value);return text.length>150?text.slice(0,150)+'…':text;},
  chartText(value){
    if(typeof value==='string')return value.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#x27;'}[c])).replace(/&lt;(\/?(?:br|b|i|extra))\s*\/?&gt;/g,'<$1>');
    if(Array.isArray(value))return value.map(UI.chartText);
    if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,UI.chartText(item)]));
    return value;
  },
  tabs(parent,labels,selected,activate){
    parent.classList.add('tabs');parent.setAttribute('role','tablist');
    const buttons=labels.map((text,index)=>{const button=UI.node('button',text);button.id=parent.id+'-'+index;button.setAttribute('role','tab');parent.append(button);return button;});
    function choose(text){if(!labels.includes(text))text=labels[0];buttons.forEach((button,i)=>{const active=labels[i]===text;button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;});activate(text,buttons[labels.indexOf(text)]);}
    buttons.forEach((button,index)=>{button.onclick=()=>choose(labels[index]);button.onkeydown=e=>{if(!['ArrowRight','ArrowLeft','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?labels.length-1:(index+(e.key==='ArrowRight'?1:-1)+labels.length)%labels.length;buttons[next].click();buttons[next].focus();};});choose(selected);return choose;
  },
};
