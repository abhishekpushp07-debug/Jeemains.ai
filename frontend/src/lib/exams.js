export const EXAMS = [
  {slug:'jee-main', name:'JEE Main', short:'JEE', eyebrow:'YOUR IIT / NIT PATHWAY', description:'Build your foundation. Then bring it all together.', subjects:['Physics','Chemistry','Mathematics']},
  {slug:'bitsat', name:'BITSAT', short:'BITS', eyebrow:'YOUR BITS PATHWAY', description:'Make every concept count. Find your pace.', subjects:['Physics','Chemistry','Mathematics','English','Logical reasoning']},
  {slug:'comedk', name:'COMEDK', short:'COMEDK', eyebrow:'YOUR ENGINEERING PATHWAY', description:'Focus on the fundamentals. Move forward with clarity.', subjects:['Physics','Chemistry','Mathematics']},
];
export const examBySlug = slug => EXAMS.find(e=>e.slug===slug);
export const examByName = name => EXAMS.find(e=>e.name===name);
export const safeExamReturn = (path, fallback) => typeof path==='string' && /^\/exams\/(jee-main|bitsat|comedk)\/(mocks|chapters|results)(\?[^#]*)?$/.test(path) ? path : fallback;
export const examPath = name => {const e=examByName(name);return e?'/exams/'+e.slug:'/home'};
