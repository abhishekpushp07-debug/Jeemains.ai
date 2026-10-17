"""Descriptive analytics only, with transparent denominators and no unsupported readiness claims."""
def insights(result):
    groups={}
    for q in result['questions']:
        if q['outcome'] in ('dropped','bonus'): continue
        label=q.get('topic') or q.get('subject') or 'Untagged'
        g=groups.setdefault(label,{'label':label,'count':0,'attempted':0,'correct':0,'incorrect':0,'skipped':0,'questions':[]})
        g['count']+=1; g[q['outcome']]+=1
        if q['outcome']!='skipped': g['attempted']+=1
        if q['outcome'] in ('incorrect','skipped'): g['questions'].append(q['number'])
    priorities=sorted((g for g in groups.values() if g['questions']),key=lambda g:(-len(g['questions']),g['label']))[:5]
    for g in priorities:
        g['accuracy']=round(100*g['correct']/g['attempted'],1) if g['attempted'] else None
        g['evidence']='Limited sample' if g['count']<5 else 'This attempt only'
        g['action']='Read the matched explanations, then use an untimed mistake retry.' if g['incorrect'] else 'Review these unattempted questions before an untimed retry.'
    return {'priorities':priorities,'basis':'Accepted server answers and the supplied frozen key only. Topic names come from source tags; subject is used when topics are absent. Not a mastery estimate, predicted rank, or official percentile. Per-question timing is not collected.'}
