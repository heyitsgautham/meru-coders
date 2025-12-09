import React from 'react';

const LGLabTest: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 via-white to-amber-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-5xl font-bold text-orange-600 mb-4">
          🔬 L-G Laboratory Test
        </h1>
        <p className="text-xl text-gray-700">
          If you can see this, the routing is working!
        </p>
        <div className="mt-8 p-6 bg-white rounded-lg shadow">
          <h2 className="text-2xl font-bold mb-4">Test Successful</h2>
          <p>The page is loading correctly. Now checking component imports...</p>
        </div>
      </div>
    </div>
  );
};

export default LGLabTest;
