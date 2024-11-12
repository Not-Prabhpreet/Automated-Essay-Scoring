import React from 'react';
import { Github, Heart } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="w-full py-6 mt-auto border-t border-gray-200 dark:border-gray-800 transition-colors duration-200">
      <div className="container mx-auto px-4">
        <div className="h-16 flex items-center justify-center sm:justify-between flex-wrap gap-4">
          <div className="text-gray-600 dark:text-gray-400">
            © {new Date().getFullYear()} Essay Scorer
          </div>
          
          <div className="flex items-center text-gray-600 dark:text-gray-400">
            Made with <Heart className="mx-2 h-5 w-5 text-blue-600 dark:text-blue-400 animate-pulse" fill="currentColor" /> by Prabh
          </div>
          
          <a
            href="https://github.com/yourusername/essay_scorer"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors duration-200"
          >
            <Github className="h-5 w-5" />
            <span>Source Code</span>
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;