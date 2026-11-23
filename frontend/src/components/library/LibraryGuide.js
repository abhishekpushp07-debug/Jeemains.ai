import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronDown,LifeBuoy,ShieldCheck,Upload} from 'lucide-react';

const when=t=>t?new Date(t*1000).toLocaleDateString('en-IN',{dateStyle:'medium'}):'';
const NEXT=[
 ['JEE Main chapter-wise PYQ','/super-admin/exam/jee-main/jee-main:chapters','Chapter-wise Tests mein Upload PDF kijiye. Har chapter apne aap apna alag test ban jata hai.'],
 ['JEE Main All India Test Series','/super-admin/exam/jee-main/jee-main:aits','Aapki 50 dates (9 Dec – 27 Jan) rakhi gayi hain. Paper upload kijiye, phir Din order se bharo dabaiye.'],
 ['BITSAT chapter-wise PYQ','/super-admin/exam/bitsat/bitsat:chapters','JEE Main jaisa hi: ek PDF, har chapter ka ek test.'],
 ['BITSAT All India Test Series','/super-admin/exam/bitsat','BITSAT kholiye, All India Test Series type jodiye, uski dates chuniye, phir upload kijiye.'],
];

// Plain rules of the Library and, after the fresh start, what to upload next.
export function LibraryGuide({fresh}){
 const [open,setOpen]=useState(()=>localStorage.getItem('library-guide-closed')!=='1');
 function toggle(){setOpen(o=>{localStorage.setItem('library-guide-closed',o?'1':'0');return !o;});}
 const c=fresh?.counts||{};
 return <section className="library-guide" data-testid="library-guide-panel">
  <button type="button" className="library-guide-head" onClick={toggle} aria-expanded={open} data-testid="library-guide-toggle">
   <LifeBuoy size={18} aria-hidden="true"/><strong>Library kaise kaam karti hai{fresh?' · aage kya karna hai':''}</strong><ChevronDown size={18} className={open?'is-open':''} aria-hidden="true"/>
  </button>
  {open&&<div className="library-guide-grid">
   <div className="library-guide-card"><h3><ShieldCheck size={16}/>Recycle bin jaisa: jab tak aap Delete na dabayein, kuch nahi jata</h3><ul>
    <li><strong>Students yahan ka kuch bhi</strong> na dekh sakte hain, na shuru kar sakte hain.</li>
    <li><strong>Har student ka purana score</strong> aur result uski history mein rehta hai.</li>
    <li><strong>Restore</strong> test ko bilkul wahin wapas rakhta hai jahan woh tha: Live test Live wapas aata hai, Draft, Draft ki tarah.</li>
    <li>All India paper apne din par wapas jata hai agar woh din abhi khali hai; warna bina din ke wapas aata hai.</li>
   </ul></div>
   <div className="library-guide-card" data-testid="library-next-steps"><h3><Upload size={16}/>{fresh?`Fresh start ho gaya ${when(fresh.finished_at)}`:'Naye tests jodna'}</h3>
    {fresh&&<p data-testid="library-fresh-summary">{(c.tests||0)+((c.series||{}).papers||0)} test yahan aaye. Students ko ab sirf {c.kept||0} JEE Main PYQ paper dikhte hain. Rapid Fire ko chhua nahi gaya.</p>}
    <ol>{NEXT.map(([t,to,h],i)=><li key={to}><Link to={to} data-testid={'library-next-'+i}>{t}</Link><small>{h}</small></li>)}</ol>
   </div>
  </div>}
 </section>;
}
