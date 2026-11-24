import React, { useEffect, useState } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Github, Moon, Sun } from 'lucide-react';

export const REPO_URL = 'https://github.com/Not-Prabhpreet/Automated-Essay-Scoring';

function Mark() {
  return (
    <svg viewBox="0 0 32 32" className="h-7 w-7" aria-hidden="true">
      <rect width="32" height="32" rx="7" className="fill-accent" />
      <path d="M9 22.5l9.5-9.5 3.5 3.5-9.5 9.5H9v-3.5z" className="fill-paper" />
      <path d="M20 11.5l1.8-1.8a1.4 1.4 0 012 0l1.5 1.5a1.4 1.4 0 010 2L23.5 15z" className="fill-paper" />
    </svg>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains('dark'));
  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);
  const toggle = () => {
    const next = !dark;
    localStorage.setItem('theme', next ? 'dark' : 'light');
    setDark(next);
  };
  return (
    <button
      onClick={toggle}
      className="grid h-8 w-8 shrink-0 place-items-center rounded-lg sm:h-9 sm:w-9 text-ink2 hover:bg-sunk hover:text-ink"
      aria-label={dark ? 'Switch to light theme' : 'Switch to dark theme'}
      title={dark ? 'Light theme' : 'Dark theme'}
    >
      {dark ? <Sun className="h-[18px] w-[18px]" /> : <Moon className="h-[18px] w-[18px]" />}
    </button>
  );
}

const navClass = ({ isActive }) =>
  `whitespace-nowrap rounded-lg px-1.5 py-2 text-[14px] transition-colors sm:px-3 sm:text-[15px] ${
    isActive ? 'bg-sunk text-ink' : 'text-ink2 hover:text-ink hover:bg-sunk/60'
  }`;

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-rule bg-paper/85 backdrop-blur">
      <div className="container-page flex h-16 items-center justify-between gap-2">
        <Link to="/" className="flex shrink-0 items-center gap-2">
          <Mark />
          <span className="whitespace-nowrap font-serif text-[16px] font-semibold tracking-tight max-[339px]:hidden sm:text-[19px]">Essay Grader</span>
        </Link>
        <nav className="flex items-center gap-0.5 sm:gap-1">
          <NavLink to="/grade" className={navClass}>Grade</NavLink>
          <NavLink to="/how-it-works" className={navClass}>How it works</NavLink>
          <a href={REPO_URL} target="_blank" rel="noreferrer" className="hidden rounded-lg px-3 py-2 text-[15px] text-ink2 hover:bg-sunk/60 hover:text-ink sm:inline-flex sm:items-center sm:gap-1.5">
            <Github className="h-4 w-4" /> Code
          </a>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-24 border-t border-rule">
      <div className="container-page flex flex-col gap-3 py-8 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
        <p>
          Built by Prabh. Trained on the{' '}
          <a className="link" href="https://www.kaggle.com/c/asap-aes" target="_blank" rel="noreferrer">ASAP</a>{' '}
          essays (Hewlett Foundation), scored by human raters.
        </p>
        <a className="link inline-flex items-center gap-1.5" href={REPO_URL} target="_blank" rel="noreferrer">
          <Github className="h-4 w-4" /> Source on GitHub
        </a>
      </div>
    </footer>
  );
}

export function ScrollToTop() {
  const { pathname, hash } = useLocation();
  useEffect(() => {
    if (hash) {
      document.getElementById(hash.slice(1))?.scrollIntoView();
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname, hash]);
  return null;
}
