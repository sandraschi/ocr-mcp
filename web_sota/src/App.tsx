import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Import } from '@/pages/import';
import { Scanner } from '@/pages/scanner';
import { Process } from '@/pages/process';
import { Editor } from '@/pages/editor';
import { Status } from '@/pages/status';
import { Help } from '@/pages/help';
import { Chat } from '@/pages/chat';
import { Settings } from '@/pages/settings';

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
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
