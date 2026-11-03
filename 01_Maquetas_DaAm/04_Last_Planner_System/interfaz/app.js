'use strict';
let current={};
function send(type,extra={}){window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*')}
function resize(){send('streamlit:setFrameHeight',{height:Math.ceil(document.documentElement.getBoundingClientRect().height)})}
function change(key,value){send('streamlit:setComponentValue',{value:{...current,[key]:value},dataType:'json'})}
window.addEventListener('message',event=>{if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;const p=event.data.args.payload;if(!p)return;current=p.state;
 document.querySelector('#title').textContent=p.names[current.page];document.querySelector('#project').textContent=p.project;
 document.querySelector('#horizon').textContent=current.page===1?p.horizon:p.cut;
 document.querySelector('nav').innerHTML='';p.names.forEach((name,i)=>{const b=document.createElement('button');b.textContent=name;b.className=i===current.page?'active':'';b.setAttribute('aria-current',i===current.page?'page':'false');b.onclick=()=>change('page',i);document.querySelector('nav').appendChild(b)});
 const filters=document.querySelector('#filters');filters.innerHTML='';p.filters.forEach(f=>{const label=document.createElement('label');label.textContent=f.label;const select=document.createElement('select');select.setAttribute('aria-label',f.label);select.id=f.key;f.options.forEach(o=>{const option=document.createElement('option');option.value=o.value;option.textContent=o.label;option.selected=String(current[f.key])===String(o.value);select.appendChild(option)});select.onchange=()=>change(f.key,select.value);label.appendChild(select);filters.appendChild(label)});
 document.querySelector('#body').innerHTML=p.body;resize();
});
new ResizeObserver(resize).observe(document.body);send('streamlit:componentReady',{apiVersion:1});window.addEventListener('load',resize);
