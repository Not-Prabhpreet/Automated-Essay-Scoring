import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import ThemeToggle from './ThemeToggle';

const Navbar = () => {
  const location = useLocation();
  
  const isActiveLink = (path) => {
    return location.pathname === path;
  };

  const linkClass = (path) =>
    `px-4 py-2 rounded-md transition-colors duration-200 ${
      isActiveLink(path)
        ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-200'
        : 'text-gray-600 hover:bg-blue-50 dark:text-gray-300 dark:hover:bg-blue-900/50'
    }`;

  return (
    <nav className="sticky top-0 z-50 w-full bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-xl font-bold text-blue-600 dark:text-blue-400">
              Essay Scorer
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <Link to="/" className={linkClass('/')}>
              Home
            </Link>
            <Link to="/score" className={linkClass('/score')}>
              Score
            </Link>
            <Link to="/about" className={linkClass('/about')}>
              About
            </Link>
            <div className="ml-4">
              <ThemeToggle />
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;