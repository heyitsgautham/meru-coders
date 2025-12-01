export function MandalaBackground() {
  return (
    <div className="fixed inset-0 -z-10">
      {/* Base gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-amber-50 via-orange-50 to-red-50" />
      
      {/* Mandala pattern overlay */}
      <div className="absolute inset-0 opacity-[0.03]">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="mandala" x="0" y="0" width="400" height="400" patternUnits="userSpaceOnUse">
              {/* Central circle */}
              <circle cx="200" cy="200" r="150" fill="none" stroke="#b45309" strokeWidth="1" />
              <circle cx="200" cy="200" r="120" fill="none" stroke="#b45309" strokeWidth="0.5" />
              <circle cx="200" cy="200" r="90" fill="none" stroke="#b45309" strokeWidth="1" />
              <circle cx="200" cy="200" r="60" fill="none" stroke="#b45309" strokeWidth="0.5" />
              
              {/* Petals */}
              {Array.from({ length: 8 }).map((_, i) => {
                const angle = (i * 45 * Math.PI) / 180;
                const x1 = 200 + Math.cos(angle) * 60;
                const y1 = 200 + Math.sin(angle) * 60;
                const x2 = 200 + Math.cos(angle) * 150;
                const y2 = 200 + Math.sin(angle) * 150;
                return (
                  <g key={i}>
                    <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#b45309" strokeWidth="0.5" />
                    <ellipse 
                      cx={200 + Math.cos(angle) * 105} 
                      cy={200 + Math.sin(angle) * 105} 
                      rx="25" 
                      ry="45" 
                      fill="none" 
                      stroke="#b45309" 
                      strokeWidth="0.5"
                      transform={`rotate(${i * 45} ${200 + Math.cos(angle) * 105} ${200 + Math.sin(angle) * 105})`}
                    />
                  </g>
                );
              })}
              
              {/* Inner star */}
              {Array.from({ length: 12 }).map((_, i) => {
                const angle = (i * 30 * Math.PI) / 180;
                const x = 200 + Math.cos(angle) * 40;
                const y = 200 + Math.sin(angle) * 40;
                return (
                  <circle key={`star-${i}`} cx={x} cy={y} r="2" fill="#b45309" />
                );
              })}
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#mandala)" />
        </svg>
      </div>

      {/* Warm gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-amber-500/5 to-orange-500/10" />
    </div>
  );
}
