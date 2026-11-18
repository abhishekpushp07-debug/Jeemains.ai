import React, { useState } from 'react';
import { NotebookPen, History, Loader2, Check } from 'lucide-react';
import { toast } from 'sonner';
import { put } from '../../lib/api';
import { Block } from './parts';

const HINTS = ['Jaise: Easy sawaal pehle round mein hi pakke karunga', 'Jaise: 50% se kam yakeen ho to jawab nahi dunga', 'Jaise: Ek sawaal par Par time ke 2 guna se zyada nahi'];

// Is test se 3 seekh: private to the student, shown again on the next mock's analysis.
export function Learnings({ id, an }) {
  const l = an.learnings || { mine: [], previous: null };
  const [items, setItems] = useState(() => [0, 1, 2].map(i => l.mine[i] || ''));
  const [busy, setBusy] = useState(false);
  const [saved, setSaved] = useState(l.mine.length > 0);
  const change = (i, v) => { setSaved(false); setItems(old => old.map((x, k) => (k === i ? v.slice(0, 140) : x))); };
  const save = async () => {
    setBusy(true);
    try {
      const r = await put(`/attempts/${id}/learnings`, { items: items.map(x => x.trim()).filter(Boolean) });
      setItems([0, 1, 2].map(i => r.items[i] || ''));
      setSaved(true);
      toast.success('3 seekh save ho gayi. Agle mock ke analysis mein yeh dobara dikhengi.');
    } catch (e) { toast.error(e.message); } finally { setBusy(false); }
  };
  const prev = l.previous;
  return (
    <Block id="learnings" kicker="SIRF AAPKE LIYE" title="Is test se meri 3 seekh" note="Apne shabdon mein likho. Report PDF mein bhi aayengi aur agle mock par yaad dilayi jaayengi.">
      {prev && (
        <div className="a2-prev-notes" data-testid="a2-learnings-previous">
          <History size={16} aria-hidden="true" />
          <div><b>Pichhle mock ({prev.title || 'mock'}) mein aapne likha tha:</b>
            <ol>{prev.items.map((x, i) => <li key={i}>{x}</li>)}</ol>
            <small>Kya is baar inpar amal hua? Neeche ke hisaab se khud check karo.</small>
          </div>
        </div>
      )}
      <div className="a2-notes">
        {items.map((v, i) => (
          <label key={i} className="a2-note">
            <span>{i + 1}</span>
            <input value={v} maxLength={140} placeholder={HINTS[i]} onChange={e => change(i, e.target.value)} data-testid={'a2-learning-input-' + i} aria-label={'Seekh ' + (i + 1)} />
          </label>
        ))}
      </div>
      <div className="a2-row">
        <button type="button" className="btn btn-primary a2-save" disabled={busy || saved} onClick={save} data-testid="a2-learnings-save">
          {busy ? <Loader2 size={16} className="spin" /> : saved ? <Check size={16} /> : <NotebookPen size={16} />} {saved ? 'Saved' : 'Save karo'}
        </button>
        <small className="a2-muted">Yeh sirf aap dekh sakte ho.</small>
      </div>
    </Block>
  );
}
