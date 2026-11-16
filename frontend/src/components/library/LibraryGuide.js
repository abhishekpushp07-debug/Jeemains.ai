import React,{useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronDown,LifeBuoy,ShieldCheck,Upload} from 'lucide-react';

const when=t=>t?new Date(t*1000).toLocaleDateString('en-IN',{dateStyle:'medium'}):'';
const NEXT=[
 ['JEE Main chapter-wise PYQ','/super-admin/exam/jee-main/jee-main:chapters','Upload PDF in Chapter-wise Tests. Each chapter becomes its own test by itself.'],
 ['JEE Main All India Test Series','/super-admin/exam/jee-main/jee-main:aits','Your 62 dates are kept. Upload the papers, then press Fill days in order.'],
 ['BITSAT chapter-wise PYQ','/super-admin/exam/bitsat/bitsat:chapters','Same as JEE Main: one PDF, one test per chapter.'],
 ['BITSAT All India Test Series','/super-admin/exam/bitsat','Open BITSAT, add the type All India Test Series, choose its dates, then upload.'],
];

// Plain rules of the Library and, after the fresh start, what to upload next.
export function LibraryGuide({fresh}){
 const [open,setOpen]=useState(()=>localStorage.getItem('library-guide-closed')!=='1');
 function toggle(){setOpen(o=>{localStorage.setItem('library-guide-closed',o?'1':'0');return !o;});}
 const c=fresh?.counts||{};
 return <section className="library-guide" data-testid="library-guide-panel">
  <button type="button" className="library-guide-head" onClick={toggle} aria-expanded={open} data-testid="library-guide-toggle">
   <LifeBuoy size={18} aria-hidden="true"/><strong>How the Library works{fresh?' · what to do next':''}</strong><ChevronDown size={18} className={open?'is-open':''} aria-hidden="true"/>
  </button>
  {open&&<div className="library-guide-grid">
   <div className="library-guide-card"><h3><ShieldCheck size={16}/>Like a recycle bin: nothing leaves unless you press Delete</h3><ul>
    <li><strong>Students cannot see or start</strong> anything in here.</li>
    <li><strong>Every student keeps their old score</strong> and result in their history.</li>
    <li><strong>Restore</strong> puts a test back exactly where it was: a Live test comes back Live, a Draft comes back as a Draft.</li>
    <li>An All India paper goes back on its day if the day is still free; otherwise it comes back without a day.</li>
   </ul></div>
   <div className="library-guide-card" data-testid="library-next-steps"><h3><Upload size={16}/>{fresh?`Fresh start done ${when(fresh.finished_at)}`:'Adding new tests'}</h3>
    {fresh&&<p data-testid="library-fresh-summary">{(c.tests||0)+((c.series||{}).papers||0)} tests moved here. Students now see only the {c.kept||0} JEE Main PYQ papers. Rapid Fire was not touched.</p>}
    <ol>{NEXT.map(([t,to,h],i)=><li key={to}><Link to={to} data-testid={'library-next-'+i}>{t}</Link><small>{h}</small></li>)}</ol>
   </div>
  </div>}
 </section>;
}
