import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { api } from '../lib/api';
import { PageTitle, Loading, ErrorBox } from '../components/Shared';
import { Button } from '../components/ui/button';
import { CompareBody } from '../components/analysis/CompareBody';

// Compare screen from the leaderboard: you against one student. Totals only.
export default function Compare() {
  const { id, key } = useParams();
  const [d, setD] = useState(null);
  const [error, setError] = useState('');
  const [tick, setTick] = useState(0);
  useEffect(() => {
    let on = true, timer;
    setError('');
    api(`/competitions/${id}/compare/${key}`)
      .then(x => { if (!on) return; setD(x); if (!x.compare.available && x.class?.state !== 'sealed' && tick < 5) timer = setTimeout(() => setTick(v => v + 1), 2500); })
      .catch(e => on && setError(e.message));
    return () => { on = false; clearTimeout(timer); };
  }, [id, key, tick]);
  return (
    <div className="container page a2-compare-page" data-testid="compare-page">
      <Button asChild variant="link" className="p-0 mb-5"><Link to={'/competitions/' + id} data-testid="compare-back"><ArrowLeft size={16} /> Leaderboard</Link></Button>
      <PageTitle eyebrow="COMPARE" title={d?.compare.available ? `Aap vs ${d.compare.label}` : 'Compare'} description={d?.title} />
      <ErrorBox error={error} retry={() => setTick(v => v + 1)} />
      {!d && !error && <Loading text="Compare khul raha hai…" />}
      {d && <CompareBody an={{ you: d.you, compare: d.compare, copy: d.copy, overview: d.you }} part="all" />}
      {d && <div className="a2-row wrap"><Button asChild variant="outline"><Link to={'/results/' + d.attempt_id} data-testid="compare-open-analysis">Apna poora analysis kholo</Link></Button></div>}
      <p className="import-fineprint mt-6" data-testid="compare-privacy-note">Sirf totals aur averages compare hote hain. Doosre student ke jawab, naam ya phone number kabhi nahi dikhte.</p>
    </div>
  );
}
