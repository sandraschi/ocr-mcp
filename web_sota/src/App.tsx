import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { AiSettingsPage } from "@/components/llm/AiSettingsPage";
import { AppsPage } from "@/pages/apps";
import { BookPipeline } from "@/pages/book-pipeline";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Depot } from "@/pages/depot";
import { Editor } from "@/pages/editor";
import { FormFillerPage } from "@/pages/form-filler";
import { Help } from "@/pages/help";
import { Inbox } from "@/pages/inbox";
import { Logger } from "@/pages/logger";
import { ScanViewerPage } from "@/pages/scan-viewer";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Status } from "@/pages/status";
import { Tools } from "@/pages/tools";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/forms" element={<FormFillerPage />} />
          <Route path="/depot" element={<Depot />} />
          <Route path="/scan-viewer" element={<ScanViewerPage />} />
          <Route path="/book-pipeline" element={<BookPipeline />} />
          <Route path="/editor" element={<Editor />} />
          <Route path="/status" element={<Status />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/logs" element={<Logger />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/ai-settings" element={<AiSettingsPage />} />
          <Route path="apps" element={<AppsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
