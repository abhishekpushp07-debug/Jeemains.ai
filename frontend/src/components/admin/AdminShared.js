import React,{useEffect,useState} from 'react';
import {Link} from 'react-router-dom';
import {ChevronRight,MapPin,Loader2} from 'lucide-react';
import {Dialog,DialogContent,DialogTitle,DialogDescription} from '../ui/dialog';
import {Button} from '../ui/button';
import {Input} from '../ui/input';
import {Label} from '../ui/label';
import {post} from '../../lib/api';
import {invalidateCatalog} from '../../lib/catalog';
import {usePageTitle} from '../../lib/pageMeta';
import {toast} from 'sonner';

const TONES={uploading:'processing',received:'processing',reading:'processing',matching:'processing',publishing:'processing',queued:'processing',organising:'processing',
 held:'attention',attention_needed:'attention',chapters_needed:'attention',done:'ready',failed:'attention',blocked:'attention',interrupted:'attention',
 ready:'ready',published:'live',live:'live',scheduled:'scheduled',unlive:'hidden',paused:'hidden',draft:'hidden',hidden:'hidden',removed:'hidden',ended:'ended',archived:'hidden'};
const LABELS={chapters_needed:'Chapter mark karo',done:'Padh li',uploading:'Upload ho raha hai',received:'Mil gayi',reading:'Padh rahe hain',matching:'Jaanch chal rahi hai',publishing:'Live ho raha hai…',queued:'Line mein',organising:'Jama rahe hain',held:'Ruka hua',attention_needed:'Dhyan chahiye',failed:'Dhyan chahiye',blocked:'Dhyan chahiye',interrupted:'Dhyan chahiye',ready:'Taiyaar',published:'Live',live:'Live',scheduled:'Scheduled',unlive:'Unlive',paused:'Ruka hua',draft:'Draft',hidden:'Chhupa',removed:'Hata diya',ended:'Khatam',archived:'Library mein'};
export const StatusChip=({state,label,testId})=><span className={'admin-chip tone-'+(TONES[state]||'hidden')} data-testid={testId}><i aria-hidden="true"/>{label||LABELS[state]||state}</span>;

export const DestinationChip=({exam,section,large,testId='destination-chip'})=><span className={'admin-destination'+(large?' is-large':'')} data-testid={testId}><MapPin size={large?18:14} aria-hidden="true"/><span>{exam}</span><ChevronRight size={14} aria-hidden="true"/><strong>{section}</strong></span>;

export const AdminCrumbs=({items})=><nav className="admin-crumbs" aria-label="Breadcrumb" data-testid="admin-breadcrumb">{items.map((item,i)=><React.Fragment key={i}>{i>0&&<ChevronRight size={14} aria-hidden="true"/>}{item.to&&i<items.length-1?<Link to={item.to} data-testid={'admin-crumb-'+i}>{item.label}</Link>:<span aria-current={i===items.length-1?'page':undefined} data-testid={'admin-crumb-'+i}>{item.label}</span>}</React.Fragment>)}</nav>;

export const AdminHeading=({title,text,action,testId})=>{usePageTitle(title);return <header className="admin-heading"><div><h1 data-testid={testId}>{title}</h1>{text&&<p>{text}</p>}</div>{action}</header>;};

const STEPS=['Kahan jayega','File ka type','Details','Upload aur padhai','Student preview'];
export const StepBar=({step})=><ol className="admin-steps" data-testid="upload-step-bar">{STEPS.map((label,i)=><li key={label} className={i+1===step?'is-current':i+1<step?'is-done':''} data-testid={'upload-step-'+(i+1)} aria-current={i+1===step?'step':undefined}><span>{i+1}</span><em>{label}</em></li>)}</ol>;

export const StudentPath=({exam,section})=><p className="admin-student-path" data-testid="student-path">Website aur App: <span>Home</span><ChevronRight size={14}/><span>{exam}</span><ChevronRight size={14}/><strong>{section}</strong></p>;

function AdminDialog({open,onClose,title,text,testId,busy,canSave,onSave,button,children}){
 return <Dialog open={open} onOpenChange={v=>!v&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid={testId}><DialogTitle>{title}</DialogTitle>{text&&<DialogDescription>{text}</DialogDescription>}<form className="admin-form" onSubmit={e=>{e.preventDefault();if(canSave&&!busy)onSave();}}>{children}<div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid={testId+'-cancel'}>Cancel</Button><Button type="submit" disabled={busy||!canSave} data-testid={testId+'-save'}>{busy&&<Loader2 size={16} className="spin"/>}{button}</Button></div></form></DialogContent></Dialog>;
}

export function ConfirmDialog({open,onClose,title,text,button,onConfirm,busy,testId='confirm-dialog'}){
 return <AdminDialog open={open} onClose={onClose} title={title} text={text} testId={testId} busy={busy} canSave onSave={onConfirm} button={button}/>;
}

const COLORS=['teal','amber','violet','rose','lime','sky'];
export function ExamDialog({open,onClose,onCreated}){
 const [name,setName]=useState(''),[short,setShort]=useState(''),[subjects,setSubjects]=useState('Physics, Chemistry, Mathematics'),[color,setColor]=useState('teal'),[busy,setBusy]=useState(false);
 async function save(){setBusy(true);try{const exam=await post('/admin/catalog/exams',{name:name.trim(),short:short.trim(),subjects:subjects.split(',').map(s=>s.trim()).filter(Boolean),color});invalidateCatalog();toast.success(`${exam.name} ban gaya. Jab tak aap Home par dikhao nahi dabate, students ko nahi dikhega.`);setName('');setShort('');onCreated(exam);onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title="Naya exam" text="Naya exam tab tak students se chhupa rehta hai jab tak aap Home par dikhao nahi dabate." testId="exam-dialog" busy={busy} canSave={name.trim().length>=2&&short.trim()&&subjects.trim()} onSave={save} button="Exam banao">
  <Label htmlFor="exam-name">Exam ka naam</Label><Input id="exam-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} placeholder="jaise NEET" data-testid="exam-name-input"/>
  <Label htmlFor="exam-short">Chhota naam</Label><Input id="exam-short" value={short} maxLength={16} onChange={e=>setShort(e.target.value)} placeholder="jaise NEET" data-testid="exam-short-input"/>
  <Label htmlFor="exam-subjects">Subjects, comma laga kar</Label><Input id="exam-subjects" value={subjects} maxLength={300} onChange={e=>setSubjects(e.target.value)} data-testid="exam-subjects-input"/>
  <fieldset className="admin-swatches"><legend>Home card ka rang</legend>{COLORS.map(c=><label key={c} className={'admin-swatch exam-color-'+c+(color===c?' is-picked':'')} data-testid={'exam-color-'+c}><input type="radio" name="exam-color" value={c} checked={color===c} onChange={()=>setColor(c)}/><span className="sr-only">{c}</span></label>)}</fieldset>
 </AdminDialog>;
}

export function SectionDialog({open,onClose,exam,onCreated}){
 const [name,setName]=useState(''),[description,setDescription]=useState(''),[layout,setLayout]=useState('list'),[busy,setBusy]=useState(false);
 async function save(){setBusy(true);try{const section=await post(`/admin/catalog/exams/${exam.slug}/sections`,{name:name.trim(),description:description.trim(),layout});invalidateCatalog();toast.success(`${section.name} ${exam.name} mein jud gaya. Live test aate hi students ko dikhega.`);setName('');setDescription('');onCreated(section);onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title={`${exam?.name||''} mein naya section`} text="Students ko section tabhi dikhta hai jab usme kam se kam ek Live test ho." testId="section-dialog" busy={busy} canSave={name.trim().length>=2} onSave={save} button="Section banao">
  <Label htmlFor="section-name">Section ka naam</Label><Input id="section-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} placeholder="jaise Revision Tests" data-testid="section-name-input"/>
  <Label htmlFor="section-description">Ek line ka description</Label><Input id="section-description" value={description} maxLength={160} onChange={e=>setDescription(e.target.value)} placeholder="Students ko yahan kya milega" data-testid="section-description-input"/>
  <fieldset className="admin-layouts"><legend>Tests kaise dikhein</legend>{[['list','Seedhi list','Mock Tests jaisa'],['chapters','Subject › chapter','Chapter-wise Tests jaisa']].map(([v,l,h])=><label key={v} className={layout===v?'is-picked':''} data-testid={'section-layout-'+v}><input type="radio" name="section-layout" value={v} checked={layout===v} onChange={()=>setLayout(v)}/><strong>{l}</strong><small>{h}</small></label>)}</fieldset>
 </AdminDialog>;
}

export function TextDialog({open,onClose,title,label,value,maxLength=160,onSave,testId='rename-dialog'}){
 const [text,setText]=useState(value||''),[busy,setBusy]=useState(false);
 useEffect(()=>{if(open)setText(value||'');},[open,value]);
 async function save(){setBusy(true);try{await onSave(text.trim());onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title={title} testId={testId} busy={busy} canSave={text.trim().length>=2&&text.trim()!==value} onSave={save} button="Save"><Label htmlFor={testId+'-input'}>{label}</Label><Input id={testId+'-input'} value={text} maxLength={maxLength} onChange={e=>setText(e.target.value)} data-testid={testId+'-input'}/></AdminDialog>;
}
