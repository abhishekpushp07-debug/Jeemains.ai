import React from 'react';
import {Link} from 'react-router-dom';
import {Compass,ArrowRight} from 'lucide-react';

export default function Mission(){
 return <div className="container page app-page" data-testid="mission-page">
  <header className="app-page-head"><span className="app-kicker">JEELIVE.AI · MISSION</span><h1 data-testid="mission-title">Mission</h1><p>Jald aa raha hai.</p></header>
  <section className="feature-dark soon-card mission-card" data-testid="mission-coming-soon"><span className="mission-icon"><Compass size={30} strokeWidth={1.6}/></span><span className="sf-chip"><i/>COMING SOON</span><h2>Your mission is on its way.</h2><p>Tab tak, aaj ka ek focused mock do.</p><Link className="sf-cta" to="/home" data-testid="mission-find-mock">Find today’s mock<ArrowRight size={19}/></Link></section>
 </div>;
}
