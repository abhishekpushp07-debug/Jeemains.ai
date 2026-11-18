// Our Mission: the maker's share card with a red "Please share karo" button above and below it, the student's impact,
// then the full story and the fine print.
import React, { useRef } from 'react';
import { Share2 } from 'lucide-react';
import { ICONS, ImpactPanel, MissionCard, ShareCta, useMissionShare } from '../components/mission/MissionCard';
import { POINTS, useMissionStats } from '../components/mission/missionApi';
import '../mission.css';

export default function Mission() {
  const card = useRef(null);
  const mission = useMissionStats();
  const { busy, note, share } = useMissionShare(card, mission.caption, undefined, !mission.loading);
  const button = where => <ShareCta testId={`mission-share-${where}`} title="Please share karo" busy={busy} onClick={() => share(true)} />;
  return <div className="ms-page" data-testid="mission-page">
    <header className="ms-page-head"><small>JEELIVE.AI · OUR MISSION</small><h1>Ek share, kisi ki free taiyari</h1></header>
    <div className="ms-layout">
      <div className="ms-col">
        <ImpactPanel stats={mission.stats} loading={mission.loading} />
        {button('top')}
        <div className="ms-card-wrap"><MissionCard ref={card} helped={mission.stats?.helped} name={mission.name} /></div>
        {button('bottom')}
        <button type="button" className="ms-more light" onClick={() => share(false)} disabled={busy} data-testid="mission-share-more"><Share2 size={16} />Doosre app mein share karo</button>
        {note ? <p className="ms-note light" role="status" data-testid="mission-share-note">{note}</p> : null}
      </div>
      <div className="ms-col">
        <h2 className="ms-section">Poori baat</h2>
        <ul className="ms-points" data-testid="mission-points">{POINTS.map(([icon, title, body], i) => { const I = ICONS[icon]; return <li key={title} style={{ '--i': i }}>
          <span className="ms-point-icon"><I size={20} /></span><div><b>{title}</b><p>{body}</p></div></li>; })}</ul>
        <p className="ms-fine" data-testid="mission-disclaimer">200+ marks ek practice target hai, guarantee nahi. “PYQ DNA”, “institute se better” aur “100% made by AI Astra” creator ka design approach aur daava hai, koi independent audit nahi. Supplied solutions hi original source hain. NTA se affiliated nahi.</p>
      </div>
    </div>
  </div>;
}
