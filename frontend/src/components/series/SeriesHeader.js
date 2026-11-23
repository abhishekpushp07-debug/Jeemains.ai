import React from 'react';
import {ChevronLeft} from 'lucide-react';

export const SeriesHeader=({eyebrow,title,onBack,backTestId,titleTestId,right})=><header className="sh-header">
  <button type="button" className="sh-round" onClick={onBack} data-testid={backTestId} aria-label="Back"><ChevronLeft size={22}/></button>
  <div className="sh-header-text"><span>{eyebrow}</span><h1 data-testid={titleTestId}>{title}</h1></div>
  {right}
</header>;

export const SectionLabel=({title,right,testid})=><div className="sh-label" data-testid={testid}><h2>{title}</h2>{right}</div>;
