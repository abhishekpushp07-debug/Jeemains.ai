import React, { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';

const preference = () => {
  try { return localStorage.getItem('tejas-theme') || 'system'; }
  catch { return 'system'; }
};
const systemDark = () => window.matchMedia('(prefers-color-scheme: dark)').matches;
const applyTheme = (value) => {
  const dark = value === 'dark' || (value === 'system' && systemDark());
  document.documentElement.classList.toggle('dark', dark);
  return dark;
};
// Apply before first React paint; system preference remains live until overridden.
applyTheme(preference());

export const ThemeToggle = () => {
  const [choice, setChoice] = useState(preference);
  const [dark, setDark] = useState(() => applyTheme(choice));
  useEffect(() => {
    setDark(applyTheme(choice));
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const sync = () => setDark(applyTheme(choice));
    media.addEventListener('change', sync);
    return () => media.removeEventListener('change', sync);
  }, [choice]);
  const toggle = () => {
    const next = dark ? 'light' : 'dark';
    try { localStorage.setItem('tejas-theme', next); } catch {}
    setChoice(next);
  };
  return <Button variant="ghost" size="icon" className="theme-toggle" data-testid="theme-toggle" aria-label={`Use ${dark ? 'light' : 'dark'} theme`} onClick={toggle}>
    {dark ? <Sun size={18} /> : <Moon size={18} />}
  </Button>;
};
