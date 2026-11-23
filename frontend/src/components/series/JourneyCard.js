import React from 'react';
import {Link} from 'react-router-dom';
import {Flame,Star,Ban,Trophy,LockKeyhole,RotateCw,ArrowUpRight} from 'lucide-react';
import {TodayMarks} from './TodayMarks';
import {shortDate} from './seriesData';
import {SERIES_PATH} from '../LiveSeriesBanner';
import {JEE_SERIES_DAYS,JEE_SERIES_START_SHORT} from '../../lib/exams';

const R=46,C=2*Math.PI*R;
const Ring=({done,total})=><div className="sh-ring" role="progressbar" aria-label={`${done} of ${total} days`} aria-valuemin={0} aria-valuemax={total} aria-valuenow={done} data-testid="streak-done">
  <svg viewBox="0 0 108 108" aria-hidden="true"><defs><linearGradient id="shRingGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#FF5C8A"/><stop offset="1" stopColor="#B983FF"/></linearGradient></defs>
    <circle cx="54" cy="54" r={R} className="sh-ring-track"/><circle cx="54" cy="54" r={R} className="sh-ring-fill" stroke="url(#shRingGrad)" strokeDasharray={C} strokeDashoffset={C*(1-done/total)}/></svg>
  <strong>{done}</strong><small>/{total} days</small>
</div>;

const Fact=({icon:Icon,tone,value,label,testid})=><div className="sh-fact" data-testid={testid}><span className={'sh-fact-icon tone-'+tone}><Icon size={16}/></span><div><strong>{value}</strong><small>{label}</small></div></div>;

const Cups=({streak,total})=><div className="sh-cups" aria-label={`Cups: ${streak.milestones.filter(m=>m.earned).length} of ${streak.milestones.length} earned`}>
  <i className="sh-cups-line"/><i className="sh-cups-fill" style={{width:Math.min(100,streak.best_streak/total*100)+'%'}}/>
  {streak.milestones.map(m=><span key={m.days} className={'sh-cup'+(m.earned?' on':'')} style={{left:Math.min(100,m.days/total*100)+'%'}} data-testid={'streak-cup-'+m.days} title={`${m.title} cup · ${m.days} days in a row`}><b>{m.earned?<Trophy size={12}/>:<LockKeyhole size={12}/>}</b><small>{m.days}d</small></span>)}
</div>;

function note(s){
  if(s.stage==='prelaunch')return `Starts ${shortDate(s.first_date)}. No early points, no pretend progress.`;
  if(s.stage==='finished')return `${s.completed_count} live days completed. Your cups stay yours.`;
  if(s.today_state==='completed')return 'Today, you showed up. Day saved.';
  if(s.today_state==='in_progress')return 'You’re on the track. Finish today’s live test.';
  return 'Complete today’s live test to add one more day.';
}

export function GuestJourney(){
  return <section className="sh-glow sh-glow-pink sh-journey" data-testid="streak-signin-card"><div className="sh-journey-body">
    <div className="sh-journey-top"><Ring done={0} total={JEE_SERIES_DAYS}/>
      <div className="sh-facts">
        <Fact testid="streak-current" icon={Flame} tone="flame" value="0-day streak" label="current"/>
        <Fact testid="streak-best" icon={Star} tone="gold" value="Best 0" label="longest run"/>
        <Fact testid="streak-skipped" icon={Ban} tone="miss" value="0 skipped" label="days missed"/>
      </div></div>
    <p className="sh-journey-note">Starts {JEE_SERIES_START_SHORT}. Sign in to save your streak, marks and analysis.</p>
    <div className="sh-marks-row is-single"><Link className="sh-red is-action" to={'/login?next='+encodeURIComponent(SERIES_PATH)} data-testid="streak-signin-link"><span className="sh-red-body"><strong>Track my journey</strong><ArrowUpRight size={18}/></span></Link></div>
  </div></section>;
}

export function JourneyCard({streak,today,error,retry}){
  if(error&&!streak)return <div className="sh-load" role="status" data-testid="streak-error">Your streak couldn’t load. Your submissions are safe.<button type="button" data-testid="streak-retry" onClick={retry}><RotateCw size={15}/>Retry</button></div>;
  if(!streak)return <div className="sh-load sh-skeleton" role="status" data-testid="streak-loading">Loading your real progress…</div>;
  const total=streak.total_days,skipped=streak.days.filter(d=>d.state==='missed').length;
  return <section className="sh-glow sh-glow-pink sh-journey" data-testid="streak-journey"><div className="sh-journey-body">
    <div className="sh-journey-top"><Ring done={streak.completed_count} total={total}/>
      <div className="sh-facts">
        <Fact testid="streak-current" icon={Flame} tone="flame" value={`${streak.current_streak}-day streak`} label="current"/>
        <Fact testid="streak-best" icon={Star} tone="gold" value={`Best ${streak.best_streak}`} label="longest run"/>
        <Fact testid="streak-skipped" icon={Ban} tone="miss" value={`${skipped} skipped`} label="days missed"/>
      </div></div>
    <p className="sh-journey-note" data-testid="streak-note">{note(streak)}</p>
    <TodayMarks today={today} streak={streak}/>
    <Cups streak={streak} total={total}/>
  </div></section>;
}
