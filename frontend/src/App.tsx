import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { ChatBotProvider } from "./contexts/ChatBotContext";
import MainApp from "./views/MainApp";
import { LandingPage } from "./views/LandingPage";
import LoginPage from "./components/LoginPage";
import SignupPage from "./components/SignupPage";
import AdminLoginPage from "./components/AdminLoginPage";
import OAuthCallback from "./components/OAuthCallback";
import Profile from "./components/Profile";
import ContributionForm from "./components/ContributionForm";
import AdminPanel from "./components/AdminPanel";
import FloatingChatbot from "./components/chat/FloatingChatbot";
import { CommunityPage, PostView, UserProfile } from "./components/community";
import { ModerationPanel } from "./components/community/ModerationPanel";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ChatBotProvider>
          <Routes>
            {/* Landing Page */}
            <Route path="/" element={<LandingPage onLaunchApp={() => {}} />} />
            
            {/* Main Application */}
            <Route path="/app" element={<MainApp />} />
            
            {/* Authentication Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/admin-login" element={<AdminLoginPage />} />
            <Route path="/oauth/callback" element={<OAuthCallback />} />
            
            {/* User Routes */}
            <Route path="/profile" element={<Profile />} />
            <Route path="/contribute" element={<ContributionForm />} />
            
            {/* Community */}
            <Route path="/community" element={<CommunityPage />} />
            <Route path="/community/post/:postId" element={<PostView />} />
            <Route path="/community/user/:userId" element={<UserProfile />} />
            
            {/* Admin Routes */}
            <Route path="/admin" element={<AdminPanel />} />
            <Route path="/admin/moderation" element={<ModerationPanel />} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
          
          {/* Global Floating Chatbot - Available on all pages */}
          <FloatingChatbot />
        </ChatBotProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}