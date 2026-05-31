import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Editor } from "@/pages/editor";
import { Help } from "@/pages/help";
import { Import } from "@/pages/import";
import { Process } from "@/pages/process";
import { ScanViewerPage } from "@/pages/scan-viewer";
import { Scanner } from "@/pages/scanner";
import { Settings } from "@/pages/settings";
import { Status } from "@/pages/status";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/import" element={<Import />} />
          <Route path="/scanner" element={<Scanner />} />
          <Route path="/process" element={<Process />} />
          <Route path="/editor" element={<Editor />} />
          <Route path="/status" element={<Status />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/scan-viewer" element={<ScanViewerPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
