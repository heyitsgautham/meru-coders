import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.merucoders.chandas',
  appName: 'Chandas Identifier',
  webDir: 'dist',
  server: {
    // For local development - use your machine's IP
    // Comment this out for production builds
    // url: 'http://YOUR_LOCAL_IP:8080',
    cleartext: true // Allow HTTP for development
  },
  android: {
    allowMixedContent: true, // For development with local API
    backgroundColor: '#FF9933'
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#FF9933',
      androidSplashResourceName: 'splash',
      androidScaleType: 'CENTER_CROP'
    }
  }
};

export default config;
