export const profileDrafts = (userId) => {
  if (!userId) return [];
  const prefix = `tejas-draft-${userId}-`;
  try {
    return Object.keys(localStorage).filter(key => key.startsWith(prefix)).map(key => {
      try {
        const answers = JSON.parse(localStorage.getItem(key) || '{}');
        const meta = JSON.parse(localStorage.getItem(key.replace('tejas-draft-', 'tejas-draft-meta-')) || '{}');
        return { key, attemptId:key.slice(prefix.length), answers, meta, count:Object.keys(answers).length };
      } catch { return { key, attemptId:key.slice(prefix.length), answers:{}, meta:{}, count:1, corrupt:true }; }
    }).filter(d => d.count > 0);
  } catch { return []; }
};
export const discardProfileDraft = (draft) => {
  localStorage.removeItem(draft.key);
  localStorage.removeItem(draft.key.replace('tejas-draft-', 'tejas-draft-meta-'));
};
