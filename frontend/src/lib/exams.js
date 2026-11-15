export const EXAMS = [
  {slug:'jee-main', name:'JEE Main', short:'JEE', eyebrow:'YOUR IIT / NIT PATHWAY', description:'Build your foundation. Then bring it all together.', subjects:['Physics','Chemistry','Mathematics']},
  {slug:'bitsat', name:'BITSAT', short:'BITS', eyebrow:'YOUR BITS PATHWAY', description:'Make every concept count. Find your pace.', subjects:['Physics','Chemistry','Mathematics','English','Logical reasoning']},
  {slug:'comedk', name:'COMEDK', short:'COMEDK', eyebrow:'YOUR ENGINEERING PATHWAY', description:'Focus on the fundamentals. Move forward with clarity.', subjects:['Physics','Chemistry','Mathematics']},
];
const CUSTOM = new Map();
export const registerExams = items => items.forEach(e => {
  if (!e.builtin) CUSTOM.set(e.slug, {slug:e.slug, key:e.key, name:e.name, short:e.short, eyebrow:`YOUR ${e.short.toUpperCase()} PATHWAY`, description:'Your tests, organised in one place.', subjects:e.subjects, color:e.color, shown:e.shown, custom:true});
});
export const examBySlug = slug => EXAMS.find(e=>e.slug===slug) || CUSTOM.get(slug);
export const examByName = name => EXAMS.find(e=>e.name===name) || [...CUSTOM.values()].find(e=>e.key===name||e.name===name);
export const safeExamReturn = (path, fallback) => typeof path==='string' && (/^\/exams\/[a-z0-9-]{2,48}\/[a-z0-9-]{2,48}(\?[^#]*)?$/.test(path)||/^\/series\/[a-z0-9-]{2,80}(\?[^#]*)?$/.test(path)||/^\/profile(\?[^#]*)?$/.test(path)) ? path : fallback;
export const JEE_SERIES = 'all-india-jee-2026-27';
export const seriesPath = id => id===JEE_SERIES ? '/series/all-india-jee' : '/series/'+id;
export const examPath = name => {const e=examByName(name);return e?'/exams/'+e.slug:'/home'};
