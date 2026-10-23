import React from 'react';
import {Lock} from 'lucide-react';

const Row=({name,d,testId})=><tr data-testid={testId}><th scope="row">{name}</th><td>{d.score} / {d.maximum}</td><td>{d.correct}</td><td>{d.incorrect}</td><td>{d.skipped}</td></tr>;
const slug=s=>s.toLowerCase().replace(/[^a-z]+/g,'-');

export const MockSectionScores=({s})=>{
 if(!s.sections)return null;
 const m=s.main_block,b=s.bonus_block;
 return <section className="card mock-section-scores" data-testid="results-mock-section-scores">
  <h3>Section-wise scores</h3>
  <div className="mock-section-table-wrap"><table className="mock-section-table">
   <thead><tr><th scope="col">Section</th><th scope="col">Score</th><th scope="col">Correct</th><th scope="col">Wrong</th><th scope="col">Unanswered</th></tr></thead>
   <tbody>
    {s.sections.map(x=><Row key={x.name} name={x.name} d={x} testId={'results-section-'+slug(x.name)}/>)}
    <Row name={`Main total (${m.count})`} d={m} testId="results-section-main-total"/>
    {b.entered?<Row name={`Bonus (${b.count})`} d={b} testId="results-section-bonus"/>:<tr data-testid="results-section-bonus-not-entered"><th scope="row">Bonus ({b.count})</th><td colSpan={4}><Lock size={13}/> Not entered · opens only after all {m.count} main questions are answered</td></tr>}
   </tbody>
  </table></div>
  <p className="import-fineprint">Total score includes bonus marks when the bonus section was entered. Same marking: +3 correct, −1 wrong, 0 unanswered.</p>
 </section>;
};
