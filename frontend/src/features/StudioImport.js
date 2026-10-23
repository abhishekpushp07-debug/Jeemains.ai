import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { FileText, FileSpreadsheet, Upload, ArrowRight, ArrowLeft, Download, ShieldCheck, Clock3, RefreshCw, CheckCircle2, X, CalendarDays, Radio, Copy, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Switch } from '../components/ui/switch';
import { Progress } from '../components/ui/progress';
import { Skeleton } from '../components/ui/skeleton';
import { api, post, downloadFile } from '../lib/api';
import { useAuth } from '../lib/auth';
import { ErrorBox, Confirm } from '../components/Shared';
import { MathText, QuestionContent } from '../components/QuestionContent';
import { ChapterBookUploader } from './ChapterBookStudio';
import { toast } from 'sonner';

const ist = (value) => value ? new Date(value * 1000).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) + ' IST' : 'Not scheduled';
const statuses = { queued: 'Queued', organising: 'Organising', ready: 'Ready to schedule', blocked: 'Needs attention', failed: 'Processing failed', interrupted: 'Processing interrupted', scheduled: 'Scheduled', live: 'Live', unlive: 'Unlive', ended: 'Ended', archive: 'Practice archive' };
export const ImportStatus = ({ value, testid }) => <span data-testid={testid} className={`import-status import-status-${value}`}><span />{statuses[value] || value}</span>;

const SourcePicker = ({ role, title, format, file, onChange, disabled }) => {
  const ref = useRef();
  const [error, setError] = useState('');
  function choose(next) {
    setError('');
    if (next && (!next.name.toLowerCase().endsWith('.' + format) || next.size > (format === 'pdf' ? 50 : 5) * 1024 * 1024)) {
      setError(`Choose a .${format} file under ${format === 'pdf' ? 50 : 5} MB.`); return;
    }
    onChange(next);
  }
  const Icon = format === 'pdf' ? FileText : FileSpreadsheet;
  return <section className={`import-dropzone ${file ? 'has-file' : ''}`} data-testid={`studio-create-test-${role}-dropzone`} onDragOver={e => e.preventDefault()} onDrop={e => { e.preventDefault(); if (!disabled) choose(e.dataTransfer.files[0]); }}>
    <div className="import-file-heading"><span className="import-icon"><Icon size={23} /></span><strong data-testid={`import-label-${role}`}>{title}</strong></div>
    <p className="import-filename" data-testid={`import-file-${role}`}>{file ? file.name : 'Drop your file here, or browse'}</p>
    <small data-testid={`import-file-size-${role}`}>{file ? `${(file.size / 1024).toFixed(1)} KB · Selected` : `${format.toUpperCase()} · up to ${format === 'pdf' ? '50' : '5'} MB`}</small>
    <Input ref={ref} type="file" accept={'.' + format} className="import-file-input" tabIndex={-1} disabled={disabled} aria-label={title} data-testid={`import-input-${role}`} onChange={e => choose(e.target.files[0])} />
    <div className="flex flex-wrap gap-2 mt-4"><Button variant="outline" disabled={disabled} data-testid={`import-browse-${role}`} onClick={() => ref.current.click()}>{file ? 'Replace file' : 'Browse file'}</Button>{file && <Button variant="ghost" disabled={disabled} data-testid={`import-remove-${role}`} onClick={() => { choose(null); ref.current.value = ''; }} aria-label={`Remove ${title}`}><X size={16} /></Button>}</div>
    {error && <p role="alert" className="import-error" data-testid={`import-file-error-${role}`}>{error}</p>}
  </section>;
};

export const StudioImportHub = () => {
  const [format, setFormat] = useState('chapter');
  const [layout, setLayout] = useState('one');
  const [questions, setQuestions] = useState(null);
  const [solutions, setSolutions] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [items, setItems] = useState(null);
  const [listError, setListError] = useState('');
  const key = useRef(null);
  const nav = useNavigate();
  const { user } = useAuth();
  const load = useCallback(() => { setListError(''); api('/studio/imports').then(d => setItems(d.items)).catch(e => setListError(e.message)); }, []);
  useEffect(load, [load]);
  function select(setter, file) { setter(file); key.current = null; setError(''); }
  function mode(value) { setFormat(value); setQuestions(null); setSolutions(null); key.current = null; setError(''); }
  async function upload() {
    setBusy(true); setError('');
    key.current ||= crypto.randomUUID();
    const form = new FormData();
    form.append('request_id', key.current); form.append('format', format); form.append('questions', questions);
    if (solutions && (format === 'pdf' || layout === 'two')) form.append('solutions', solutions);
    try { const result = await api('/studio/imports', { method: 'POST', body: form }); nav('/studio/imports/' + result.id); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  if (format === 'chapter') return <div data-testid="studio-import-hub"><Tabs value={format} onValueChange={mode} className="chapter-import-modes"><TabsList><TabsTrigger value="chapter" data-testid="studio-create-test-import-mode-chapter">Chapter book · 1 PDF</TabsTrigger><TabsTrigger value="pdf" data-testid="studio-create-test-import-mode-pdf">PDF question + solution files</TabsTrigger><TabsTrigger value="xlsx" data-testid="studio-create-test-import-mode-excel">Excel · direct text</TabsTrigger></TabsList></Tabs><ChapterBookUploader/></div>;
  const download = variant => downloadFile('/studio/imports/template?variant=' + variant, `jeemains-ai-${variant}-template.xlsx`).catch(e => toast.error(e.message));
  return <div className="import-hub" data-testid="studio-import-hub">
    <section className="import-card">
      <div className="import-section-label"><Upload size={16} /> FROM YOUR CONTENT TO THEIR NEXT ATTEMPT</div>
      <h2 data-testid="studio-import-heading">Your files. A ready-to-attempt test.</h2>
      <p className="import-muted" data-testid="studio-import-description">Upload once. We organise the questions and match the solutions. You choose when students start.</p>
      <Tabs value={format} onValueChange={mode} className="mt-6" data-testid="studio-create-test-import-mode-tabs"><TabsList><TabsTrigger disabled={busy} value="chapter" data-testid="studio-create-test-import-mode-chapter">Chapter book · 1 PDF</TabsTrigger><TabsTrigger disabled={busy} value="pdf" data-testid="studio-create-test-import-mode-pdf"><FileText size={16} /> PDF files</TabsTrigger><TabsTrigger disabled={busy} value="xlsx" data-testid="studio-create-test-import-mode-excel"><FileSpreadsheet size={16} /> Excel · direct text</TabsTrigger></TabsList></Tabs>
      {format === 'xlsx' && <div className="import-excel-help" data-testid="studio-excel-help"><strong>Questions, options, answers and solutions—as text.</strong><p>Use the template headers. One workbook can contain a combined Questions sheet or separate Questions and Solutions sheets.</p>
        <div className="import-template-actions"><Button variant="outline" data-testid="studio-create-test-excel-template-download-button" onClick={() => download('combined')}><Download size={16} /> Combined template</Button><Button variant="ghost" data-testid="import-template-sheets" onClick={() => download('sheets')}>Two-sheet template</Button></div>
        <Tabs value={layout} onValueChange={v => { setLayout(v); setSolutions(null); key.current = null; }}><TabsList><TabsTrigger disabled={busy} value="one" data-testid="excel-layout-one">One workbook</TabsTrigger><TabsTrigger disabled={busy} value="two" data-testid="excel-layout-two">Two files</TabsTrigger></TabsList></Tabs>
        {layout === 'two' && <div className="flex flex-wrap gap-2 mt-2"><Button variant="link" data-testid="import-template-questions" onClick={() => download('questions')}>Questions template</Button><Button variant="link" data-testid="import-template-solutions" onClick={() => download('solutions')}>Solutions template</Button></div>}
      </div>}
      <div className={`import-dropzones ${format === 'xlsx' && layout === 'one' ? 'single' : ''}`}>
        <SourcePicker key={format + '-q'} role="questions" title={format === 'pdf' ? 'Questions PDF' : layout === 'one' ? 'Questions + solutions workbook' : 'Questions workbook'} format={format} file={questions} onChange={v => select(setQuestions, v)} disabled={busy} />
        {(format === 'pdf' || layout === 'two') && <SourcePicker key={format + '-s'} role="solutions" title={format === 'pdf' ? 'Solutions PDF' : 'Solutions workbook'} format={format} file={solutions} onChange={v => select(setSolutions, v)} disabled={busy} />}
      </div>
      <p className="import-fineprint" data-testid="import-format-note">{format === 'pdf' ? 'Searchable PDFs with numbered questions and explicit answer keys. Plain text is imported directly; equations and diagrams keep their original PDF layout. Numbered solution steps are kept inside their matched solution. Scans need a searchable PDF.' : 'Up to 300 questions · .xlsx only · Plain cell values, not formulas or embedded images. Basic $LaTeX$ supported. Missing or conflicting entries are flagged.'}</p>
      <ErrorBox error={error} />
      <div className="import-submit-row"><Button className="btn btn-primary" data-testid={format === 'pdf' ? 'studio-create-test-organise-button' : 'studio-create-test-excel-validate-button'} disabled={busy || user.role !== 'owner' || !questions || ((format === 'pdf' || layout === 'two') && !solutions)} onClick={upload}>{busy ? <><RefreshCw className="spin" size={16} /> Uploading privately…</> : <>{format === 'pdf' ? 'Organise & Preview' : 'Validate & Preview'}<ArrowRight size={17} /></>}</Button><span className="import-fineprint">{user.role !== 'owner' ? 'Owner access is required to upload and schedule.' : 'No test metadata forms. Just your files.'}</span></div>
      <p className="import-fineprint mt-4" data-testid="import-rights-note">By uploading, you confirm permission to use this content with your students and include it in their personal reports. Source keys are retained—not independently verified or generated.</p>
    </section>
    <aside className="import-card import-recent">
      <div className="import-section-label"><Clock3 size={16} /> YOUR TESTS</div><h2>From draft to live.</h2>
      <div className="import-mini-steps"><span>01 Upload</span><ArrowRight size={12} /><span>02 Organise</span><ArrowRight size={12} /><span>03 Schedule</span></div>
      {listError ? <><ErrorBox error={listError} /><Button variant="outline" onClick={load} data-testid="import-list-retry">Retry list</Button></> : !items ? <div className="space-y-3"><Skeleton className="h-20" /><Skeleton className="h-20" /></div> : items.length ? <div className="import-recent-list">{items.map(item => <Link className="import-recent-item" to={'/studio/imports/' + item.id} key={item.id} data-testid={'import-open-' + item.id}><ImportStatus value={item.status} testid={'import-status-' + item.id} /><strong>{item.title}</strong><small>{item.count} questions · {item.format.toUpperCase()}</small><small>{ist(item.start_at)}</small><ArrowRight size={16} /></Link>)}</div> : <div className="import-empty" data-testid="import-list-empty"><FileStackIcon /><strong>Your next test starts here.</strong><p>Upload your first PDF pair or Excel workbook. Its progress and schedule will appear here.</p></div>}
      <div className="import-assurance"><ShieldCheck size={18} /><p>Uncertain pairings never go live. Fix flagged source entries and upload again.</p></div>
    </aside>
  </div>;
};
const FileStackIcon = () => <FileSpreadsheet size={30} />;

export default function StudioImport() {
  const { id } = useParams(); const { user } = useAuth();
  const [record, setRecord] = useState(null); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [date, setDate] = useState(''); const [time, setTime] = useState(''); const [confirm, setConfirm] = useState(false); const [page, setPage] = useState(0); const [tab, setTab] = useState('preview');
  const load = useCallback(async () => { const d = await api('/studio/imports/' + id); setRecord(d); return d; }, [id]);
  useEffect(() => { let disposed = false; let timeout; const check = async () => { try { const d = await api('/studio/imports/' + id); if (disposed) return; setRecord(d); if (['queued', 'organising'].includes(d.status)) timeout = setTimeout(check, 2500); } catch (e) { if (!disposed) setError(e.message); } }; check(); return () => { disposed = true; clearTimeout(timeout); }; }, [id]);
  useEffect(() => { if (record?.start_at) { const local = new Date(record.start_at * 1000 + 330 * 60000).toISOString(); setDate(local.slice(0,10)); setTime(local.slice(11,16)); } }, [record?.start_at]);
  async function perform(fn, message) { setBusy(true); setError(''); try { const d = await fn(); setRecord(d); if (message) toast.success(message); setConfirm(false); } catch (e) { setError(e.message); } finally { setBusy(false); } }
  if (!record) return <div className="container page"><ErrorBox error={error} />{error ? <Button data-testid="import-detail-retry" onClick={() => load().catch(e => setError(e.message))}>Retry</Button> : <Skeleton className="h-64" />}</div>;
  const complete = ['ready','scheduled','live','unlive','ended','archive'].includes(record.status);
  const canSchedule = complete && (!record.start_at || record.start_at > record.server_now);
  const start = async () => { if (!date || !time) { setError('Choose both the start date and time (IST).'); return; } await perform(() => post('/studio/imports/' + id + '/schedule', { start_at: `${date}T${time}:00+05:30`, revision: record.revision }), 'Schedule saved. Students can start at the chosen time.'); };
  const shown = record.questions.slice(page * 10, page * 10 + 10);
  return <div className="container page import-detail" data-testid="studio-organiser-detail">
    <Button asChild variant="link" className="p-0 mb-6"><Link to="/studio" data-testid="studio-organiser-breadcrumb"><ArrowLeft size={16} /> Content Studio</Link></Button>
    <div className="import-title-row"><div><div className="import-section-label">{record.format.toUpperCase()} IMPORT · CUSTOM PRACTICE</div><h1 data-testid="import-test-title">{record.title}</h1><p className="import-muted" data-testid="import-test-facts">{record.exam} · {record.count} questions · {record.duration_minutes} minutes · +{record.exam === 'BITSAT' ? 3 : 4} / −1 marking</p></div><ImportStatus value={record.status} testid="studio-organiser-status-badge" /></div>
    <ErrorBox error={error} />
    <div className="import-detail-grid">
      <section className="import-main">
        <div className="import-card" aria-live="polite"><div className="import-section-label"><CheckCircle2 size={16} /> ORGANISATION</div><Progress value={complete ? 100 : record.status === 'queued' ? 15 : record.status === 'organising' ? 50 : 75} data-testid="studio-organiser-progress" className="my-4" /><div className="import-mini-steps" data-testid="studio-organiser-stepper"><span>Upload</span><span>Extract</span><span>Pair</span><span>Validate</span><span>Ready</span></div><p className="import-muted mt-4" data-testid="import-processing-message">{record.message}</p>
          {['failed','interrupted','queued'].includes(record.status) && <Button variant="outline" disabled={busy || user.role !== 'owner'} data-testid="import-processing-retry" onClick={() => perform(async () => { await post('/studio/imports/' + id + '/retry'); return load(); }, 'Retry requested. Use Refresh to check progress.')}><RefreshCw size={16} /> Retry processing</Button>}
          <Button variant="ghost" disabled={busy} data-testid="import-refresh" onClick={() => perform(load)}><RefreshCw size={15} /> Refresh</Button>
        </div>
        <div className="import-card">
          <Tabs value={tab} onValueChange={setTab}><TabsList data-testid="studio-excel-preview-tabs"><TabsTrigger value="preview" data-testid="studio-excel-preview-tab-valid">Pairing preview ({record.count})</TabsTrigger><TabsTrigger value="issues" data-testid="studio-excel-preview-tab-errors">Issues ({record.issues.length})</TabsTrigger></TabsList></Tabs>
          {tab === 'issues' ? <div className="mt-6">{record.issues.length ? <><p className="import-muted">Correct the listed cells or source entries, then upload again. Scheduling stays locked.</p><div className="import-issue-list" data-testid="studio-excel-error-table">{record.issues.map((e,i) => <div className="import-issue" key={i} data-testid={'import-issue-' + i}><strong>{e.sheet || 'Source'}{e.row ? ` · Row ${e.row}` : e.question ? ` · Q${e.question}` : ''}{e.field ? ` · ${e.field}` : ''}</strong><p>{e.message}</p></div>)}</div><Button variant="outline" data-testid="studio-excel-download-error-report-button" onClick={() => downloadFile('/studio/imports/' + id + '/errors', 'Tejas_import_issues.csv').catch(e => toast.error(e.message))}><Download size={16} /> Download issue report</Button></> : <p data-testid="import-no-issues">No pairing or structure issues found.</p>}</div> : <div className="mt-6">{shown.length ? shown.map(q => <details className="import-question" key={q.id} open={record.count <= 3} data-testid={'import-pair-' + q.number}><summary data-testid={'import-preview-question-' + q.number}><span>Q{q.number} · {q.subject}</span><span className="import-fineprint">{q.render_mode === 'typed' ? 'Direct text' : 'Source region'} · {q.type}</span></summary><div className="import-question-content">{q.render_reason && <p className="import-fineprint mb-4" data-testid={'import-render-reason-' + q.number}>{q.render_reason}</p>}<QuestionContent question={q} base={`/studio/imports/${id}/questions/${q.id}`} />{q.render_mode === 'typed' && q.type === 'mcq' && <div className="import-options">{Object.entries(q.options).map(([key,text]) => <div key={key} data-testid={`import-option-${q.number}-${key}`}><strong>{key}</strong><MathText text={text} /></div>)}</div>}<div className="import-solution" data-testid={'import-solution-' + q.number}><strong>Matched solution · Supplied key: {q.answer || 'Missing'}</strong><QuestionContent question={q} solution base={`/studio/imports/${id}/questions/${q.id}`} /><small>{q.pairing_evidence}</small></div></div></details>) : <p className="import-muted">Your paired questions will appear after processing.</p>}
            {record.count > 10 && <div className="flex justify-between items-center gap-3 mt-4"><Button variant="outline" disabled={!page} data-testid="import-preview-prev" onClick={() => setPage(p => p - 1)}><ChevronLeft size={16} /> Previous</Button><span data-testid="import-preview-page">{page + 1} / {Math.ceil(record.count / 10)}</span><Button variant="outline" disabled={(page+1)*10 >= record.count} data-testid="import-preview-next" onClick={() => setPage(p => p + 1)}>Next<ChevronRight size={16} /></Button></div>}
          </div>}
        </div>
      </section>
      <aside className="import-schedule import-card">
        {record.exam==='JEE Main'&&(!record.set_id||record.series_import)&&<div className="series-preflight-note" data-testid="import-series-shortcut"><strong>{record.series_date?'All India series · '+record.series_date:'For the All India JEE series'}</strong><p>{record.series_import?'Use the owner series panel to manage the day. Live attempts get the full 180 minutes; results release at 11:59 PM and archive practice opens at midnight.':'Keep this import private. After reviewing it, return to the series panel and assign its day there instead of scheduling an ordinary competition.'}</p><Button asChild variant="outline"><Link to="/studio" data-testid="import-series-manage">Open owner series panel</Link></Button>{record.series_import&&<Button asChild variant="link"><Link to="/series/all-india-jee" data-testid="import-series-student-hub">View series hub</Link></Button>}</div>}
        <div className="import-section-label"><CalendarDays size={16} /> {record.series_import?'SERIES PUBLICATION':'THE ONLY NEXT STEP'}</div><h2>{record.series_import?'Your series day':'When should it start?'}</h2><p className="import-muted" data-testid="studio-schedule-timezone-label">{record.series_import?'All India daily opening and release times are fixed in IST.':'All times in Asia/Kolkata (IST). Students share one test window; joining late means less time.'}</p>
        {!complete ? <div className="import-assurance" data-testid="import-schedule-locked"><ShieldCheck size={20} /><p>Scheduling unlocks when all questions and solutions are paired without issues.</p></div> : <>
          {canSchedule && !record.series_import && <div className="import-schedule-form"><Label htmlFor="schedule-date">Start date</Label><Input id="schedule-date" type="date" value={date} onChange={e => setDate(e.target.value)} data-testid="studio-schedule-start-date" /><Label htmlFor="schedule-time">Start time</Label><Input id="schedule-time" type="time" value={time} onChange={e => setTime(e.target.value)} data-testid="studio-schedule-start-time" /><Button className="btn btn-primary" disabled={busy || user.role !== 'owner'} data-testid="studio-schedule-submit-button" onClick={start}>{record.start_at ? 'Update schedule' : 'Schedule test'}<ArrowRight size={16} /></Button></div>}
          {record.start_at && <div className="import-window" data-testid="studio-schedule-summary"><span>Starts</span><strong>{ist(record.start_at)}</strong><span>Solutions & results unlock</span><strong>{ist(record.end_at)}</strong></div>}
          {record.set_id && !record.series_import && <div className="import-live-control"><div className="flex items-center justify-between gap-3"><Label htmlFor="live-switch" className="flex gap-2 items-center"><Radio size={18} />{record.live_enabled ? 'Live enabled' : 'Unlive'}</Label><Switch id="live-switch" className="import-live-switch" checked={record.live_enabled} disabled={busy || user.role !== 'owner' || record.status === 'ended'} onCheckedChange={() => setConfirm(true)} data-testid="studio-live-toggle-switch" /></div><p className="import-fineprint" data-testid="import-live-policy">{record.status === 'ended' ? 'This test window has ended. Results are available to submitted participants.' : record.live_enabled ? 'Automatically opens at the start time. New attempts close when the window ends.' : 'New attempts are paused. Existing attempts continue until the original deadline.'}</p><Button variant="outline" data-testid="import-copy-link" onClick={() => navigator.clipboard.writeText(window.location.origin + '/competitions/' + id).then(() => toast.success('Competition hub link copied.')).catch(() => toast.error('Could not copy. Open Competitions from the navigation.'))}><Copy size={15} /> Copy competition link</Button><Button asChild variant="link"><Link to={'/competitions/' + id} data-testid="import-open-competition">Open competition page<ArrowRight size={15} /></Link></Button></div>}
        </>}
        <Button asChild variant="ghost" className="mt-4"><Link data-testid="import-replace-sources" to="/studio">Upload new or corrected sources</Link></Button>
      </aside>
    </div>
    <Confirm open={confirm} onClose={() => setConfirm(false)} title={record.live_enabled ? 'Pause new attempts?' : 'Enable this test?'} button={record.live_enabled ? 'Make Unlive' : 'Enable Live'} busy={busy} onConfirm={() => perform(() => post('/studio/imports/' + id + '/live', { live: !record.live_enabled, revision: record.revision }), 'Test availability updated.')}><p>{record.live_enabled ? 'Students cannot start new attempts. Existing attempts and their saved answers continue with the original deadline.' : 'Students may start within the scheduled test window. Questions and solutions remain frozen.'}</p></Confirm>
  </div>;
}
