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
const LABELS={chapters_needed:'Mark chapters',done:'Read',uploading:'Uploading',received:'Received',reading:'Reading',matching:'Checking',publishing:'Publishing…',queued:'Queued',organising:'Organising',held:'Held',attention_needed:'Needs attention',failed:'Needs attention',blocked:'Needs attention',interrupted:'Needs attention',ready:'Ready',published:'Live',live:'Live',scheduled:'Scheduled',unlive:'Unlive',paused:'Paused',draft:'Draft',hidden:'Hidden',removed:'Removed',ended:'Ended',archived:'In Library'};
export const StatusChip=({state,label,testId})=><span className={'admin-chip tone-'+(TONES[state]||'hidden')} data-testid={testId}><i aria-hidden="true"/>{label||LABELS[state]||state}</span>;

export const DestinationChip=({exam,section,large,testId='destination-chip'})=><span className={'admin-destination'+(large?' is-large':'')} data-testid={testId}><MapPin size={large?18:14} aria-hidden="true"/><span>{exam}</span><ChevronRight size={14} aria-hidden="true"/><strong>{section}</strong></span>;

export const AdminCrumbs=({items})=><nav className="admin-crumbs" aria-label="Breadcrumb" data-testid="admin-breadcrumb">{items.map((item,i)=><React.Fragment key={i}>{i>0&&<ChevronRight size={14} aria-hidden="true"/>}{item.to&&i<items.length-1?<Link to={item.to} data-testid={'admin-crumb-'+i}>{item.label}</Link>:<span aria-current={i===items.length-1?'page':undefined} data-testid={'admin-crumb-'+i}>{item.label}</span>}</React.Fragment>)}</nav>;

export const AdminHeading=({title,text,action,testId})=>{usePageTitle(title);return <header className="admin-heading"><div><h1 data-testid={testId}>{title}</h1>{text&&<p>{text}</p>}</div>{action}</header>;};

const STEPS=['Where it goes','File type','Details','Upload & reading','Student preview'];
export const StepBar=({step})=><ol className="admin-steps" data-testid="upload-step-bar">{STEPS.map((label,i)=><li key={label} className={i+1===step?'is-current':i+1<step?'is-done':''} data-testid={'upload-step-'+(i+1)} aria-current={i+1===step?'step':undefined}><span>{i+1}</span><em>{label}</em></li>)}</ol>;

export const StudentPath=({exam,section})=><p className="admin-student-path" data-testid="student-path">Website and App: <span>Home</span><ChevronRight size={14}/><span>{exam}</span><ChevronRight size={14}/><strong>{section}</strong></p>;

function AdminDialog({open,onClose,title,text,testId,busy,canSave,onSave,button,children}){
 return <Dialog open={open} onOpenChange={v=>!v&&onClose()}><DialogContent className="tejas-dialog admin-dialog" data-testid={testId}><DialogTitle>{title}</DialogTitle>{text&&<DialogDescription>{text}</DialogDescription>}<form className="admin-form" onSubmit={e=>{e.preventDefault();if(canSave&&!busy)onSave();}}>{children}<div className="button-row"><Button type="button" variant="outline" onClick={onClose} data-testid={testId+'-cancel'}>Cancel</Button><Button type="submit" disabled={busy||!canSave} data-testid={testId+'-save'}>{busy&&<Loader2 size={16} className="spin"/>}{button}</Button></div></form></DialogContent></Dialog>;
}

export function ConfirmDialog({open,onClose,title,text,button,onConfirm,busy,testId='confirm-dialog'}){
 return <AdminDialog open={open} onClose={onClose} title={title} text={text} testId={testId} busy={busy} canSave onSave={onConfirm} button={button}/>;
}

const COLORS=['teal','amber','violet','rose','lime','sky'];
export function ExamDialog({open,onClose,onCreated}){
 const [name,setName]=useState(''),[short,setShort]=useState(''),[subjects,setSubjects]=useState('Physics, Chemistry, Mathematics'),[color,setColor]=useState('teal'),[busy,setBusy]=useState(false);
 async function save(){setBusy(true);try{const exam=await post('/admin/catalog/exams',{name:name.trim(),short:short.trim(),subjects:subjects.split(',').map(s=>s.trim()).filter(Boolean),color});invalidateCatalog();toast.success(`${exam.name} created. Students will not see it until you choose Show on Home.`);setName('');setShort('');onCreated(exam);onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title="New exam" text="A new exam stays hidden from students until you choose Show on Home." testId="exam-dialog" busy={busy} canSave={name.trim().length>=2&&short.trim()&&subjects.trim()} onSave={save} button="Create exam">
  <Label htmlFor="exam-name">Exam name</Label><Input id="exam-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} placeholder="e.g. NEET" data-testid="exam-name-input"/>
  <Label htmlFor="exam-short">Short name</Label><Input id="exam-short" value={short} maxLength={16} onChange={e=>setShort(e.target.value)} placeholder="e.g. NEET" data-testid="exam-short-input"/>
  <Label htmlFor="exam-subjects">Subjects, separated by commas</Label><Input id="exam-subjects" value={subjects} maxLength={300} onChange={e=>setSubjects(e.target.value)} data-testid="exam-subjects-input"/>
  <fieldset className="admin-swatches"><legend>Home card colour</legend>{COLORS.map(c=><label key={c} className={'admin-swatch exam-color-'+c+(color===c?' is-picked':'')} data-testid={'exam-color-'+c}><input type="radio" name="exam-color" value={c} checked={color===c} onChange={()=>setColor(c)}/><span className="sr-only">{c}</span></label>)}</fieldset>
 </AdminDialog>;
}

export function SectionDialog({open,onClose,exam,onCreated}){
 const [name,setName]=useState(''),[description,setDescription]=useState(''),[layout,setLayout]=useState('list'),[busy,setBusy]=useState(false);
 async function save(){setBusy(true);try{const section=await post(`/admin/catalog/exams/${exam.slug}/sections`,{name:name.trim(),description:description.trim(),layout});invalidateCatalog();toast.success(`${section.name} added to ${exam.name}. Students see it once it has a live test.`);setName('');setDescription('');onCreated(section);onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title={`New section in ${exam?.name||''}`} text="Students see a section only when it has at least one live test." testId="section-dialog" busy={busy} canSave={name.trim().length>=2} onSave={save} button="Create section">
  <Label htmlFor="section-name">Section name</Label><Input id="section-name" value={name} maxLength={60} onChange={e=>setName(e.target.value)} placeholder="e.g. Revision Tests" data-testid="section-name-input"/>
  <Label htmlFor="section-description">One-line description</Label><Input id="section-description" value={description} maxLength={160} onChange={e=>setDescription(e.target.value)} placeholder="What students will find here" data-testid="section-description-input"/>
  <fieldset className="admin-layouts"><legend>How tests are listed</legend>{[['list','Simple list','Like Mock Tests'],['chapters','Subject › chapter','Like Chapter-wise Tests']].map(([v,l,h])=><label key={v} className={layout===v?'is-picked':''} data-testid={'section-layout-'+v}><input type="radio" name="section-layout" value={v} checked={layout===v} onChange={()=>setLayout(v)}/><strong>{l}</strong><small>{h}</small></label>)}</fieldset>
 </AdminDialog>;
}

export function TextDialog({open,onClose,title,label,value,maxLength=160,onSave,testId='rename-dialog'}){
 const [text,setText]=useState(value||''),[busy,setBusy]=useState(false);
 useEffect(()=>{if(open)setText(value||'');},[open,value]);
 async function save(){setBusy(true);try{await onSave(text.trim());onClose();}catch(e){toast.error(e.message);}finally{setBusy(false);}}
 return <AdminDialog open={open} onClose={onClose} title={title} testId={testId} busy={busy} canSave={text.trim().length>=2&&text.trim()!==value} onSave={save} button="Save"><Label htmlFor={testId+'-input'}>{label}</Label><Input id={testId+'-input'} value={text} maxLength={maxLength} onChange={e=>setText(e.target.value)} data-testid={testId+'-input'}/></AdminDialog>;
}
