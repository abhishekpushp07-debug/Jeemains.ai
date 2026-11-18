import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';
import { setTheme, useTheme } from '../lib/theme';

export const ThemeToggle = () => {
  const dark = useTheme() === 'dark';
  return <Button variant="ghost" size="icon" className="theme-toggle" data-testid="theme-toggle" aria-pressed={dark} aria-label={dark ? 'Use light theme' : 'Use dark theme'} onClick={() => setTheme(dark ? 'light' : 'dark')}>
    {dark ? <Sun size={18} /> : <Moon size={18} />}
  </Button>;
};
