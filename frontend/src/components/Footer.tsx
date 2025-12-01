export function Footer() {
  return (
    <footer className="mt-10 pb-10">
      <div className="container mx-auto px-6" style={{ display: 'flex', justifyContent: 'center' }}>
        <div className="relative" style={{ textAlign: 'center' }}>
          {/* Decorative line */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-px bg-gradient-to-r from-[#fdf8f3] via-[#ff9933] to-[#fdf8f3]" />
          
          <div className="text-center pt-10 space-y-3 mx-auto">
            <p className="text-[#4a2c10] text-sm font-medium">
              Sanskrit Meter Identification System
            </p>
            <p className="text-[#9a6a3a] text-sm">
              Advanced meter analysis for Sanskrit texts
            </p>
            
            {/* Decorative dots */}
            <div className="flex items-center justify-center gap-3 pt-6">
              <div className="w-1.5 h-1.5 rounded-full bg-[#ff9933]" />
              <div className="text-[#ff9933] text-lg font-bold">॥</div>
              <div className="w-1.5 h-1.5 rounded-full bg-[#ff9933]" />
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
