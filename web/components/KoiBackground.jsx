'use client'; // Add this if using Next.js 13+ App Router

import { useEffect, useRef } from 'react';

export default function KoiCometBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    
    const COLOR_SCHEME = [
      { r: 100, g: 200, b: 255 },
      { r: 150, g: 100, b: 255 },
      { r: 50, g: 255, b: 200 },
      { r: 100, g: 150, b: 255 },
      { r: 200, g: 100, b: 255 }
    ];
    
    const COMET_COUNT = 8;
    const TRAIL_LENGTH = 120;
    
    const setCanvasSize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    
    setCanvasSize();
    window.addEventListener('resize', setCanvasSize);

    // Observe document height changes (images load, content expands, etc.)
    const ro = new ResizeObserver(() => setCanvasSize());
    ro.observe(document.body);
    
    class Comet {
      constructor() {
        this.reset();
        this.y = Math.random() * canvas.height;
        this.color = COLOR_SCHEME[Math.floor(Math.random() * COLOR_SCHEME.length)];
        this.trail = [];
      }
      
      reset() {
        this.x = -100;
        this.y = Math.random() * canvas.height;
        this.speed = (0.5 + Math.random() * 1.5) * 3.9; // ~3.9x faster (≈30% more than before)
        this.amplitude = 30 + Math.random() * 50;
        this.frequency = 0.001 + Math.random() * 0.002;
        this.size = 8 + Math.random() * 15;
        this.phase = Math.random() * Math.PI * 2;
        this.opacity = Math.min(1, (0.6 + Math.random() * 0.4) * 2.0); // ~100% brighter, capped at 1
        this.color = COLOR_SCHEME[Math.floor(Math.random() * COLOR_SCHEME.length)];
        this.trail = [];
      }
      
      update() {
        this.x += this.speed;
        this.y += Math.sin(this.x * this.frequency + this.phase) * 0.5;
        
        this.trail.unshift({ x: this.x, y: this.y });
        if (this.trail.length > TRAIL_LENGTH) {
          this.trail.pop();
        }
        
        if (this.x > canvas.width + 100) {
          this.reset();
        }
      }
      
      draw() {
        for (let i = 0; i < this.trail.length; i++) {
          const point = this.trail[i];
          const alpha = (1 - i / this.trail.length) * this.opacity;
          const size = this.size * (1 - i / this.trail.length);
          
          const gradient = ctx.createRadialGradient(
            point.x, point.y, 0,
            point.x, point.y, size
          );
          
          gradient.addColorStop(0, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha})`);
          gradient.addColorStop(0.5, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${alpha * 0.5})`);
          gradient.addColorStop(1, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0)`);
          
          ctx.fillStyle = gradient;
          ctx.beginPath();
          ctx.arc(point.x, point.y, size, 0, Math.PI * 2);
          ctx.fill();
        }
        
        const headGradient = ctx.createRadialGradient(
          this.x, this.y, 0,
          this.x, this.y, this.size * 1.5
        );
        
        headGradient.addColorStop(0, `rgba(${this.color.r + 50}, ${this.color.g + 50}, ${this.color.b + 50}, ${this.opacity})`);
        headGradient.addColorStop(0.4, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, ${this.opacity})`);
        headGradient.addColorStop(1, `rgba(${this.color.r}, ${this.color.g}, ${this.color.b}, 0)`);
        
        ctx.fillStyle = headGradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    
    const comets = [];
    for (let i = 0; i < COMET_COUNT; i++) {
      comets.push(new Comet());
    }
    
    let animationId;
    let lastTime = 0;
    function animate(ts = 0) {
      if (ts - lastTime < 33) { // ~30 FPS throttle
        animationId = requestAnimationFrame(animate);
        return;
      }
      lastTime = ts;
      ctx.fillStyle = 'rgba(10, 14, 39, 0.08)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      comets.forEach(comet => {
        comet.update();
        comet.draw();
      });
      
      animationId = requestAnimationFrame(animate);
    }
    
    animate();
    
    return () => {
      window.removeEventListener('resize', setCanvasSize);
      cancelAnimationFrame(animationId);
      ro.disconnect();
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute top-0 left-0 w-full -z-10 pointer-events-none"
      style={{ filter: 'blur(1.8px)', background: '#0a0e27' }}
    />
  );
}