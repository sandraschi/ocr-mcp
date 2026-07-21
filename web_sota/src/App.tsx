import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { BookPipeline } from "@/pages/book-pipeline";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Editor } from "@/pages/editor";
import { Help } from "@/pages/help";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/book-pipeline" element={<BookPipeline />} />
          <Route path="/editor" element={<Editor />} />
          <Route path="/status" element={<Status />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
