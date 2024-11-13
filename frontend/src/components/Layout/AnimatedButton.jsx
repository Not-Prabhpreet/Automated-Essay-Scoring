import React, { useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';

const AnimatedButton = ({ 
  to, 
  children, 
  className = '', 
  variant = 'primary',
  icon: Icon 
}) => {
  const buttonRef = useRef(null);
  const navigate = useNavigate();
  
  useEffect(() => {
    const button = buttonRef.current;
    const tl = gsap.timeline({ paused: true });
    
    // Create border elements with different colors based on variant
    const borderElements = Array.from({ length: 4 }).map(() => {
      const div = document.createElement('div');
      div.className = `absolute pointer-events-none ${
        variant === 'primary' 
          ? 'bg-white/70 dark:bg-white/70' // Light border for primary button
          : 'bg-blue-400 dark:bg-blue-500'  // Blue border for secondary button
      }`;
      button.appendChild(div);
      return div;
    });
    
    // Position the border elements
    gsap.set(borderElements[0], { top: 0, left: 0, width: 0, height: 2 }); // Top
    gsap.set(borderElements[1], { top: 0, right: 0, width: 2, height: 0 }); // Right
    gsap.set(borderElements[2], { bottom: 0, right: 0, width: 0, height: 2 }); // Bottom
    gsap.set(borderElements[3], { top: 0, left: 0, width: 2, height: 0 }); // Left

    // Create the animation
    tl.to(borderElements[0], { width: '100%', duration: 0.2 })
      .to(borderElements[1], { height: '100%', duration: 0.2 }, '-=0.1')
      .to(borderElements[2], { width: '100%', duration: 0.2 }, '-=0.1')
      .to(borderElements[3], { height: '100%', duration: 0.2 }, '-=0.1');

    const handleMouseEnter = () => {
      tl.play();
      // Add scale effect on hover
      gsap.to(button, {
        scale: 1.02,
        duration: 0.2
      });
    };

    const handleMouseLeave = () => {
      tl.reverse();
      // Remove scale effect
      gsap.to(button, {
        scale: 1,
        duration: 0.2
      });
    };

    button.addEventListener('mouseenter', handleMouseEnter);
    button.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      button.removeEventListener('mouseenter', handleMouseEnter);
      button.removeEventListener('mouseleave', handleMouseLeave);
      borderElements.forEach(el => el.remove());
    };
  }, [variant]);

  const handleClick = () => {
    if (to) {
      navigate(to);
    }
  };

  const baseStyles = "relative inline-flex items-center px-6 py-3 text-lg font-semibold rounded-md transition-all duration-200";
  const variantStyles = {
    primary: "text-white bg-blue-600 dark:bg-blue-500 hover:bg-blue-700 dark:hover:bg-blue-600",
    secondary: "text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800"
  };

  return (
    <button
      ref={buttonRef}
      onClick={handleClick}
      className={`${baseStyles} ${variantStyles[variant]} ${className}`}
    >
      {children}
      {Icon && <Icon className="ml-2 h-5 w-5" />}
    </button>
  );
};

export default AnimatedButton;