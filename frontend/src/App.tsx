/* ========== 主应用入口 ========== */
import './index.css';
import { useAuthStore } from './stores/auth-store';
import { useAppStore } from './stores/app-store';
import AuthPage from './pages/AuthPage';
import ContextHeader from './components/layout/ContextHeader';
import AgentPanel from './components/layout/AgentPanel';
import AgentChat from './components/chat/AgentChat';
import CalendarDashboard from './components/calendar/CalendarDashboard';
import ConfigDrawer from './components/config-drawer/ConfigDrawer';
import HistoryDrawer from './components/chat/HistoryDrawer';
import DatabaseManager from './components/database/DatabaseManager';
import NutritionQuotaPanel from './components/nutrition-quota/NutritionQuotaPanel';
import { useState } from 'react';
import { Clock, Database, Apple } from 'lucide-react';

function App() {
  const { token, user, logout } = useAuthStore();
  const [historyOpen, setHistoryOpen] = useState(false);
  const [dbManagerOpen, setDbManagerOpen] = useState(false);
  const [quotaPanelOpen, setQuotaPanelOpen] = useState(false);
  const resetAll = useAppStore(state => state.resetAll);

  const handleLogout = () => {
    logout();
    resetAll();
  };

  if (!token) {
    return <AuthPage onLoginSuccess={() => {}} />;
  }

  return (
    <div className="h-screen flex flex-col bg-surface">
      {/* 全局顶部栏 */}
      <header className="h-11 bg-white border-b border-border-light flex items-center px-5 shrink-0 justify-between">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center shadow-sm">
            <span className="text-white text-sm">🍽️</span>
          </div>
          <h1 className="text-sm font-bold text-text-primary tracking-wide">走云AI营养排菜</h1>
          <span className="text-xs text-text-muted hidden sm:inline">智能排菜 · 多智能体架构</span>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={() => setHistoryOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
          >
            <Clock size={16} />
            历史对话
          </button>
          
          <button
            onClick={() => setDbManagerOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
          >
            <Database size={16} />
            数据库
          </button>

          <button
            onClick={() => setQuotaPanelOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-text-secondary hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
            title="查看每日营养配额达标详情"
          >
            <Apple size={16} />
            营养达标
          </button>
          
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-primary-100 flex items-center justify-center">
              <span className="text-xs font-bold text-primary-700">{user?.username?.[0]?.toUpperCase()}</span>
            </div>
            <span className="text-sm font-medium text-text-secondary">{user?.username}</span>
          </div>
          <button 
            onClick={handleLogout} 
            className="text-xs font-medium px-3 py-1.5 rounded-lg bg-gray-50 text-text-muted hover:bg-red-50 hover:text-red-600 transition-colors"
          >
            退出登录
          </button>
        </div>
      </header>

      {/* 主体内容：左日历 + 右对话 */}
      <div className="flex-1 flex overflow-hidden">
        {/* 左侧: 日历看板 (占大部分) */}
        <main className="flex-1 min-w-0 overflow-hidden">
          <CalendarDashboard />
        </main>

        {/* 右侧: 智能体面板 + 对话 + 概览区 */}
        <aside className="w-[380px] shrink-0 border-l border-border-light bg-white flex flex-col overflow-hidden">
          {/* 全局概览 */}
          <ContextHeader />
          {/* 智能体状态面板 */}
          <div className="border-b border-border-light bg-gray-900/95">
            <AgentPanel />
          </div>
          {/* 对话窗口 */}
          <div className="flex-1 min-h-0 overflow-hidden">
            <AgentChat />
          </div>
        </aside>
      </div>

      {/* 配置抽屉 (浮层) */}
      <ConfigDrawer />
      
      {/* 历史记录抽屉 */}
      <HistoryDrawer isOpen={historyOpen} onClose={() => setHistoryOpen(false)} />
      
      {/* 数据库管理面板 */}
      <DatabaseManager isOpen={dbManagerOpen} onClose={() => setDbManagerOpen(false)} />

      {/* 营养配额达标详情面板 */}
      {quotaPanelOpen && <NutritionQuotaPanel onClose={() => setQuotaPanelOpen(false)} />}
    </div>
  );
}

export default App;
