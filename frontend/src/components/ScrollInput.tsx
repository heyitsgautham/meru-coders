import { useEffect, useRef, useState, useCallback } from "react";
import scrollCap from "../assets/e540625d16a84c3e1809b14be7e3dd57897d630d.png";
import scrollMiddleTile from "../assets/0dbdfc89a47c0e0456e507054d725251aeee1042.png";

interface ScrollInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function ScrollInput({ value, onChange, placeholder }: ScrollInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const middleRef = useRef<HTMLDivElement>(null);
  const [middleHeight, setMiddleHeight] = useState(260);

  const MIN_HEIGHT = 260;

  // Auto-resize the scroll middle section as content grows (infinite)
  const autoSize = useCallback(() => {
    const textarea = textareaRef.current;
    const middle = middleRef.current;
    if (!textarea || !middle) return;

    // Reset textarea height to get accurate scrollHeight
    textarea.style.height = "auto";
    const textHeight = textarea.scrollHeight;
    
    // Let textarea grow infinitely
    textarea.style.height = `${textHeight}px`;

    // Calculate middle section height (text + vertical padding)
    const computedStyle = getComputedStyle(middle);
    const verticalPadding = 
      parseInt(computedStyle.paddingTop, 10) + 
      parseInt(computedStyle.paddingBottom, 10);

    const newMiddleHeight = Math.max(MIN_HEIGHT, textHeight + verticalPadding);
    setMiddleHeight(newMiddleHeight);
  }, []);

  // Handle input changes
  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
    autoSize();
  };

  // Initial resize and window resize handler
  useEffect(() => {
    autoSize();
    window.addEventListener("resize", autoSize);
    return () => window.removeEventListener("resize", autoSize);
  }, [autoSize]);

  // Resize when value changes externally
  useEffect(() => {
    autoSize();
  }, [value, autoSize]);

  return (
    <div className="scroll-wrapper">
      {/* Middle parchment - expandable */}
      <div 
        ref={middleRef}
        className="scroll-middle"
        style={{ 
          backgroundImage: `url(${scrollMiddleTile})`,
          height: `${middleHeight}px`
        }}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          placeholder={placeholder || "Type or paste your Sanskrit shloka here…"}
          id="sanskrit-input"
        />
      </div>

      {/* Top roller - absolutely positioned */}
      <div 
        className="scroll-top"
        style={{ backgroundImage: `url(${scrollCap})` }}
      />

      {/* Bottom roller - absolutely positioned */}
      <div 
        className="scroll-bottom"
        style={{ backgroundImage: `url(${scrollCap})` }}
      />
    </div>
  );
}
