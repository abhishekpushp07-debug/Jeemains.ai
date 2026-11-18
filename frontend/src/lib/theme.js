import {useEffect,useState} from 'react';

const KEY='jeelive-theme',EVENT='jeelive-theme';
export const storedTheme=()=>{try{return localStorage.getItem(KEY)==='dark'?'dark':'light';}catch{return 'light';}};
export function applyTheme(theme){
 const root=document.documentElement,dark=theme==='dark';
 root.classList.toggle('dark',dark);root.classList.toggle('light',!dark);root.classList.remove('exam-light');
 root.style.background=dark?'#08080A':'#FFFFFF';root.style.colorScheme=dark?'dark':'light';
 document.querySelector('meta[name="theme-color"]')?.setAttribute('content',dark?'#08080A':'#FFFFFF');
}
export function setTheme(theme){
 try{localStorage.setItem(KEY,theme);}catch{}
 applyTheme(theme);window.dispatchEvent(new CustomEvent(EVENT,{detail:theme}));
}
export function useTheme(){
 const [theme,set]=useState(storedTheme);
 useEffect(()=>{const on=e=>set(e.detail);window.addEventListener(EVENT,on);return()=>window.removeEventListener(EVENT,on);},[]);
 return theme;
}
applyTheme(storedTheme());
