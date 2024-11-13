import React, { useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';

const AnimatedLink = ({ to, children, className = '' }) => {
  const linkRef = useRef(null);
  const lineRef = useRef(null);

  useEffect(() => {
    const link = linkRef.current;
    const line = lineRef.current;

    gsap.set(line, {
      scaleX: 0,
      transformOrigin: 'left'
    });

    const handleMouseEnter = () => {
      gsap.to(line, {
        scaleX: 1,
        duration: 0.4,
        ease: "power2.out"
      });
    };

    const handleMouseLeave = () => {
      gsap.to(line, {
        scaleX: 0,
        duration: 0.4,
        ease: "power2.in"
      });
    };

    link.addEventListener('mouseenter', handleMouseEnter);
    link.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      link.removeEventListener('mouseenter', handleMouseEnter);
      link.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <Link 
      ref={linkRef}
      to={to} 
      className={`relative group ${className}`}
    >
      {children}
      <div 
        ref={lineRef}
        className="absolute bottom-0 left-0 w-full h-[2px] bg-blue-400 dark:bg-blue-500"
        style={{ transformOrigin: 'left' }}
      />
    </Link>
  );
};

export default AnimatedLink;