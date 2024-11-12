import React, { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';

const ThemeToggle = () => {
  const [isDark, setIsDark] = useState(true); // Set default to true

  useEffect(() => {
    // Initialize with dark mode
    if (!document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    }
  }, []);

  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [isDark]);

  return (
    <button
      onClick={() => setIsDark(!isDark)}
      className="relative inline-flex items-center justify-center w-14 h-7 rounded-full bg-gradient-to-r from-blue-200 to-blue-300 dark:from-blue-700 dark:to-blue-800 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      aria-label="Toggle theme"
    >
      <div
        className={`absolute left-1 transform transition-transform duration-200 ease-out ${
          isDark ? 'translate-x-7' : 'translate-x-0'
        }`}
      >
        <div className="w-5 h-5 rounded-full bg-white dark:bg-blue-200 shadow-lg flex items-center justify-center">
          {isDark ? (
            <Moon className="w-3 h-3 text-blue-800" />
          ) : (
            <Sun className="w-3 h-3 text-yellow-500" />
          )}
        </div>
      </div>
    </button>
  );
};

export default ThemeToggle;