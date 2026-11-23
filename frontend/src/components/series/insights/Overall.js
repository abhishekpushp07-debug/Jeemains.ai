import React from 'react';
import {Dir} from './parts';

export function Overall({o,total,max}){
  const items=[['Din diye',o.days,`/${total}`],['Average marks',o.average??'—',`/${max}`],['Best',o.best??'—',`/${max}`],
    ['Average se upar',o.compared_days?o.above_average_days:'—',o.compared_days?`/${o.compared_days} din`:'']];
  return <div className="sh-card si-card" data-testid="si-overall">
    <div className="sh-stats">{items.map(([l,v,m])=><div key={l} data-testid={'si-overall-'+l.split(' ')[0].toLowerCase()}><small>{l}</small><strong>{v}{m&&<em>{m}</em>}</strong></div>)}</div>
    <div className="si-dirs"><Dir name="Marks" way={o.direction} change={o.change} testId="si-dir-marks"/><Dir name="Accuracy" way={o.accuracy_direction} change={o.accuracy_change} unit="%" testId="si-dir-accuracy"/></div>
  </div>;
}
