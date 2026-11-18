import React, { useState } from 'react';
import { Download, Share2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { fetchWithSession } from '../../lib/api';

const save = (blob, name) => {
  const url = URL.createObjectURL(blob), a = document.createElement('a');
  a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
};

export function ReportActions({ id, an }) {
  const [busy, setBusy] = useState('');
  const day = new Date((an.submitted_at || 0) * 1000).toLocaleDateString('en-CA', { timeZone: 'Asia/Kolkata' });
  const name = `JEELIVE_${(an.title || 'Mock').replace(/[^A-Za-z0-9]+/g, '_').replace(/^_|_$/g, '').slice(0, 60) || 'Mock'}_${day}`;
  const query = an.score_version && an.score_version !== 'original' ? '?score_version=' + encodeURIComponent(an.score_version) : '';
  const fetchFile = async path => {
    const res = await fetchWithSession(path);
    if (!res.ok) throw new Error('File abhi nahi ban paayi. Thodi der mein dobara try karo.');
    return res.blob();
  };
  const run = async (kind, work) => {
    setBusy(kind);
    try { await work(); } catch (e) { if (e.name !== 'AbortError') toast.error(e.message); } finally { setBusy(''); }
  };
  const report = () => run('pdf', async () => save(await fetchFile(`/attempts/${id}/analysis/report.pdf${query}`), name + '.pdf'));
  const share = () => run('png', async () => {
    const file = new File([await fetchFile(`/attempts/${id}/analysis/share.png`)], name + '.png', { type: 'image/png' });
    const o = an.overview;
    if (navigator.canShare?.({ files: [file] })) await navigator.share({ files: [file], title: an.title, text: `Mera Score ${o.score}/${o.maximum} · JEELIVE.AI` });
    else { save(file, file.name); toast.success('Scorecard download ho gaya. Ab WhatsApp par bhej sakte ho.'); }
  });
  return <>
    <button type="button" className="btn btn-secondary" data-testid="a2-download-report" disabled={!!busy} onClick={report}>{busy === 'pdf' ? <Loader2 size={16} className="spin" /> : <Download size={16} />} Report download</button>
    <button type="button" className="btn btn-secondary" data-testid="a2-share-scorecard" disabled={!!busy} onClick={share}>{busy === 'png' ? <Loader2 size={16} className="spin" /> : <Share2 size={16} />} Share</button>
  </>;
}
