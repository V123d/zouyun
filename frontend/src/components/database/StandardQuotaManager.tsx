import { useState, useEffect } from 'react';
import {
    Save, ShieldCheck, AlertCircle, Info,
    RefreshCw, Hash, Settings
} from 'lucide-react';
import { getQuotaProfiles, updateQuotaProfile } from '../../services/api';
import type { QuotaProfile } from '../../types';
import QuotaEditor from '../quota-editor/QuotaEditor';

const INGREDIENT_CATEGORIES = [
    "大米", "面粉", "畜肉", "禽肉", "禽蛋", "鱼虾", "牛奶",
    "大豆", "蔗糖", "植物油", "鲜蔬菜", "水果", "食用菌(干)", "干菜",
];

const NUTRITION_METRICS: { key: string; label: string; unit: string }[] = [
    { key: "calories", label: "卡路里", unit: "kcal/日" },
    { key: "protein", label: "蛋白质", unit: "g/日" },
    { key: "fat", label: "脂肪", unit: "g/日" },
    { key: "carbs", label: "碳水化合物", unit: "g/日" },
];

export default function StandardQuotaManager() {
    const [profiles, setProfiles] = useState<QuotaProfile[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeId, setActiveId] = useState<number | null>(null);
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [localQuotas, setLocalQuotas] = useState<Record<string, number>>({});
    const [quotaEditorOpen, setQuotaEditorOpen] = useState(false);
    const [editingProfileId, setEditingProfileId] = useState<number | undefined>(undefined);

    useEffect(() => {
        fetchData();
    }, []);

    async function fetchData() {
        setLoading(true);
        try {
            const data = await getQuotaProfiles();
            setProfiles(data);
            if (data.length > 0 && !activeId) {
                setActiveId(data[0].id);
            }
        } catch (err) {
            setError('获取数据失败');
        } finally {
            setLoading(false);
        }
    }

    const currentProfile = profiles.find((q) => q.id === activeId);
    const isNutritionProfile = currentProfile?.quota_type === "nutrition";

    useEffect(() => {
        if (currentProfile) {
            setLocalQuotas({ ...currentProfile.quotas });
        }
    }, [activeId, currentProfile?.id, currentProfile?.quota_type]);

    function handleUpdateValue(key: string, value: number) {
        setLocalQuotas(prev => ({ ...prev, [key]: value }));
    }

    async function handleSave() {
        if (!currentProfile) return;
        setIsSaving(true);
        setError(null);
        setSuccessMessage(null);
        try {
            await updateQuotaProfile(currentProfile.id, {
                quotas: localQuotas,
                quota_type: currentProfile.quota_type,
            });
            await fetchData();
            setSuccessMessage(`已保存「${currentProfile.name}」的配置`);
            setTimeout(() => setSuccessMessage(null), 3000);
        } catch (err) {
            setError('同步到后端失败');
        } finally {
            setIsSaving(false);
        }
    }

    if (loading) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-3">
                <RefreshCw className="animate-spin text-primary-500" size={24} />
                <span className="text-sm">正在加载配额配置...</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-surface/30">
            {/* 顶部页签 + 右上管理按钮 */}
            <div className="bg-white px-6 pt-4 pb-0 border-b border-border-light shadow-sm">
                <div className="flex items-center justify-between mb-0">
                    <div className="flex items-center gap-1">
                        {profiles.map((p) => (
                            <button
                                key={p.id}
                                onClick={() => setActiveId(p.id)}
                                className={`pb-3 px-3 text-sm font-bold transition-all relative flex items-center gap-1.5 ${
                                    activeId === p.id
                                        ? 'text-primary-600'
                                        : 'text-text-muted hover:text-text-secondary'
                                }`}
                            >
                                {p.name}
                                {p.is_system && (
                                    <span className="text-[8px] bg-gray-200 text-gray-500 px-1 rounded">内置</span>
                                )}
                                {activeId === p.id && (
                                    <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary-500 rounded-t-full" />
                                )}
                            </button>
                        ))}
                    </div>
                    <button
                        onClick={() => {
                            setEditingProfileId(activeId ?? undefined);
                            setQuotaEditorOpen(true);
                        }}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-border rounded-lg hover:bg-gray-50 text-text-secondary mb-2"
                    >
                        <Settings size={12} />
                        管理配额配置
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-6">
                <div className="max-w-4xl mx-auto space-y-6">
                    {error && (
                        <div className="bg-red-50 border border-red-100 text-red-600 px-4 py-3 rounded-xl flex items-center gap-2 text-sm animate-shake">
                            <AlertCircle size={18} />
                            {error}
                        </div>
                    )}
                    {successMessage && (
                        <div className="bg-green-50 border border-green-100 text-green-600 px-4 py-3 rounded-xl flex items-center gap-2 text-sm animate-in slide-in-from-top-2">
                            <ShieldCheck size={18} />
                            {successMessage}
                        </div>
                    )}

                    {currentProfile ? (
                        <>
                            <div className="flex items-center gap-3">
                                <div>
                                    <h3 className="text-sm font-bold text-text-primary">{currentProfile.name}</h3>
                                    <p className="text-[11px] text-text-muted mt-0.5">{currentProfile.description || '无描述'}</p>
                                </div>
                                <div className="ml-auto flex items-center gap-2">
                                    <span
                                        className={`text-[9px] px-2 py-0.5 rounded font-medium ${
                                            isNutritionProfile
                                                ? "bg-orange-100 text-orange-700"
                                                : "bg-green-100 text-green-700"
                                        }`}
                                    >
                                        {isNutritionProfile ? "营养值配额" : "配料分类配额"}
                                    </span>
                                    <div className="text-[10px] bg-surface px-2 py-1 rounded border border-border-light text-text-muted">
                                        共 {Object.keys(currentProfile.quotas).length}{" "}
                                        {isNutritionProfile ? "项营养素" : "个类目"}
                                    </div>
                                    {currentProfile.is_system ? (
                                        <span className="text-[10px] bg-gray-100 text-gray-400 px-2 py-1 rounded">系统内置</span>
                                    ) : (
                                        <span className="text-[10px] bg-blue-50 text-blue-500 px-2 py-1 rounded">自定义</span>
                                    )}
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {isNutritionProfile
                                    ? NUTRITION_METRICS.map(({ key, label, unit }) => (
                                          <div
                                              key={key}
                                              className="bg-white p-4 rounded-2xl border border-border-light shadow-sm hover:shadow-md transition-shadow group"
                                          >
                                              <div className="flex items-center justify-between mb-3">
                                                  <div className="flex items-center gap-2">
                                                      <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center group-hover:bg-orange-100 transition-colors">
                                                          <Hash size={14} className="text-orange-600" />
                                                      </div>
                                                      <span className="text-sm font-bold text-text-primary">{label}</span>
                                                  </div>
                                                  <div className="flex items-center gap-1.5">
                                                      <input
                                                          type="number"
                                                          min={0}
                                                          step={key === "calories" ? 1 : 0.1}
                                                          value={
                                                              localQuotas[key] ??
                                                              currentProfile.quotas[key] ??
                                                              0
                                                          }
                                                          onChange={(e) =>
                                                              handleUpdateValue(key, Number(e.target.value))
                                                          }
                                                          className="w-24 px-3 py-1.5 bg-surface border border-border rounded-lg text-sm text-right font-mono focus:border-orange-400 outline-none transition-all"
                                                      />
                                                      <span className="text-xs text-text-muted font-medium min-w-[3.5rem] text-right">
                                                          {unit}
                                                      </span>
                                                  </div>
                                              </div>
                                              <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                                                  <div
                                                      className="h-full bg-orange-400 opacity-60 transition-all duration-500"
                                                      style={{
                                                          width: `${(() => {
                                                              const v =
                                                                  localQuotas[key] ??
                                                                  currentProfile.quotas[key] ??
                                                                  0;
                                                              const capByKey: Record<string, number> = {
                                                                  calories: 24,
                                                                  protein: 0.75,
                                                                  fat: 0.67,
                                                                  carbs: 3.6,
                                                              };
                                                              const cap = capByKey[key] ?? 1;
                                                              return Math.min(100, v / cap);
                                                          })()}%`,
                                                      }}
                                                  />
                                              </div>
                                          </div>
                                      ))
                                    : INGREDIENT_CATEGORIES.map((cat: string) => (
                                          <div
                                              key={cat}
                                              className="bg-white p-4 rounded-2xl border border-border-light shadow-sm hover:shadow-md transition-shadow group"
                                          >
                                              <div className="flex items-center justify-between mb-3">
                                                  <div className="flex items-center gap-2">
                                                      <div className="w-8 h-8 rounded-lg bg-gray-50 flex items-center justify-center group-hover:bg-primary-50 transition-colors">
                                                          <Hash
                                                              size={14}
                                                              className="text-text-muted group-hover:text-primary-500"
                                                          />
                                                      </div>
                                                      <span className="text-sm font-bold text-text-primary">{cat}</span>
                                                  </div>
                                                  <div className="flex items-center gap-1.5">
                                                      <input
                                                          type="number"
                                                          min={0}
                                                          step={0.1}
                                                          value={
                                                              localQuotas[cat] ??
                                                              currentProfile.quotas[cat] ??
                                                              0
                                                          }
                                                          onChange={(e) =>
                                                              handleUpdateValue(cat, Number(e.target.value))
                                                          }
                                                          className="w-24 px-3 py-1.5 bg-surface border border-border rounded-lg text-sm text-right font-mono focus:border-primary-400 outline-none transition-all"
                                                      />
                                                      <span className="text-xs text-text-muted font-medium w-8">
                                                          g/日
                                                      </span>
                                                  </div>
                                              </div>
                                              <div className="h-1 bg-gray-100 rounded-full overflow-hidden">
                                                  <div
                                                      className="h-full bg-primary-400 opacity-60 transition-all duration-500"
                                                      style={{
                                                          width: `${Math.min(
                                                              100,
                                                              (localQuotas[cat] ||
                                                                  currentProfile.quotas[cat] ||
                                                                  0) / 5
                                                          )}%`,
                                                      }}
                                                  />
                                              </div>
                                          </div>
                                      ))}
                            </div>
                        </>
                    ) : (
                        <div className="p-12 text-center border-2 border-dashed border-border rounded-2xl">
                            <p className="text-text-muted mb-4">尚未选择配额配置</p>
                            <button
                                onClick={() => setQuotaEditorOpen(true)}
                                className="px-6 py-2 bg-primary-600 text-white rounded-xl text-sm font-bold"
                            >
                                立即初始化
                            </button>
                        </div>
                    )}

                    {/* 说明卡片 */}
                    <div className="bg-primary-50/50 border border-primary-100 rounded-2xl p-5 flex gap-4">
                        <Info className="text-primary-500 shrink-0 mt-0.5" size={20} />
                        <div>
                            <h4 className="text-sm font-bold text-primary-900 mb-1">指标说明</h4>
                            <ul className="text-xs text-primary-800/70 space-y-1.5 leading-relaxed">
                                <li>• 此标准用于"约束校验智能体"计算每日摄入达标度。</li>
                                <li>• 修改标准后，系统将自动对现有的排菜方案进行重新评估。</li>
                                <li>• 定量数值应参考《伙食费标准及食物定量标准》最新规定。</li>
                                <li>• 内置配置不可删除，自定义配置可自由增删。</li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* 底部保存条 */}
            <div className="bg-white border-t border-border-light p-4 px-6 flex items-center justify-between">
                <div className="text-xs text-text-muted flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                    云端数据已同步至：{new Date().toLocaleTimeString()}
                </div>
                <button
                    onClick={handleSave}
                    disabled={isSaving || !currentProfile}
                    className="flex items-center gap-2 px-8 py-2.5 bg-primary-600 text-white rounded-xl text-sm font-bold shadow-lg shadow-primary-200 hover:bg-primary-700 active:scale-95 transition-all disabled:opacity-50"
                >
                    {isSaving ? <RefreshCw className="animate-spin" size={16} /> : <Save size={16} />}
                    {isSaving ? '正在同步...' : `保存并应用到「${currentProfile?.name ?? ''}」`}
                </button>
            </div>

            {quotaEditorOpen && (
                <QuotaEditor
                    onClose={() => {
                        setQuotaEditorOpen(false);
                        fetchData();
                    }}
                    initialProfileId={editingProfileId}
                    onSave={(profile) => {
                        setProfiles([...profiles.filter(p => p.id !== profile.id), profile]);
                    }}
                />
            )}
        </div>
    );
}
