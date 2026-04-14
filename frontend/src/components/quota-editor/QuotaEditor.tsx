/* ========== 配额配置文件编辑器 (Quota Editor Modal) ========== */
import { useState, useEffect } from 'react';
import {
    X,
    Plus,
    Trash2,
    Edit2,
    Copy,
    Save,
    Settings,
    AlertTriangle,
    CheckCircle,
} from 'lucide-react';
import { getQuotaProfiles, createQuotaProfile, updateQuotaProfile, deleteQuotaProfile, duplicateQuotaProfile } from '../../services/api';
import type { QuotaProfile, QuotaProfileCreate } from '../../types';

interface QuotaEditorProps {
    onClose: () => void;
    /** 打开时默认选中的配置 ID */
    initialProfileId?: number;
    /** 保存后回调（传入新 profile） */
    onSave?: (profile: QuotaProfile) => void;
}

const NUTRITION_KEYS = [
    { key: 'calories', label: '卡路里', unit: 'kcal', defaultVal: 2400 },
    { key: 'protein', label: '蛋白质', unit: 'g', defaultVal: 75 },
    { key: 'fat', label: '脂肪', unit: 'g', defaultVal: 67 },
    { key: 'carbs', label: '碳水化合物', unit: 'g', defaultVal: 360 },
];

type QuotaType = 'nutrition';

export default function QuotaEditor({ onClose, initialProfileId, onSave }: QuotaEditorProps) {
    const [profiles, setProfiles] = useState<QuotaProfile[]>([]);
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [editMode, setEditMode] = useState<'view' | 'edit' | 'create'>('view');
    const [editForm, setEditForm] = useState<QuotaProfileCreate>({
        class_type: '',
        name: '',
        description: '',
        quotas: {},
        quota_type: 'nutrition',
        is_system: false,
    });
    const [nutritionForm, setNutritionForm] = useState<Record<string, string>>({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [confirmDelete, setConfirmDelete] = useState(false);

    useEffect(() => {
        loadProfiles();
    }, []);

    async function loadProfiles() {
        setLoading(true);
        setError('');
        try {
            const data = await getQuotaProfiles();
            setProfiles(data);
            if (initialProfileId) {
                setSelectedId(initialProfileId);
            } else if (data.length > 0 && !selectedId) {
                setSelectedId(data[0].id);
            }
        } catch (e: any) {
            setError('加载失败: ' + e.message);
        } finally {
            setLoading(false);
        }
    }

    function selectProfile(id: number) {
        setSelectedId(id);
        setEditMode('view');
        setError('');
        setConfirmDelete(false);
    }

    function startCreate() {
        const initQuotas: Record<string, string> = {};
        NUTRITION_KEYS.forEach(({ key, defaultVal }) => { initQuotas[key] = String(defaultVal); });
        setEditForm({
            class_type: '',
            name: '',
            description: '',
            quotas: {},
            quota_type: 'nutrition',
            is_system: false,
        });
        setNutritionForm(initQuotas);
        setEditMode('create');
        setError('');
    }

    function startEdit() {
        const profile = profiles.find(p => p.id === selectedId);
        if (!profile) return;
        setEditForm({
            class_type: profile.class_type,
            name: profile.name,
            description: profile.description,
            quotas: { ...profile.quotas },
            quota_type: 'nutrition',
            is_system: profile.is_system,
        });
        const nf: Record<string, string> = {};
        NUTRITION_KEYS.forEach(({ key, defaultVal }) => {
            const v = profile.quotas[key];
            nf[key] = String(v != null ? v : defaultVal);
        });
        setNutritionForm(nf);
        setEditMode('edit');
        setError('');
    }

    function startDuplicate() {
        const profile = profiles.find(p => p.id === selectedId);
        if (!profile) return;
        setEditForm({
            class_type: '',
            name: profile.name + ' (副本)',
            description: profile.description,
            quotas: { ...profile.quotas },
            quota_type: 'nutrition',
            is_system: false,
        });
        const nf: Record<string, string> = {};
        NUTRITION_KEYS.forEach(({ key, defaultVal }) => {
            const v = profile.quotas[key];
            nf[key] = String(v != null ? v : defaultVal);
        });
        setNutritionForm(nf);
        setEditMode('create');
        setError('');
    }

    async function handleSave() {
        let parsedQuotas: Record<string, number> = {};
        NUTRITION_KEYS.forEach(({ key }) => {
            const val = parseFloat(nutritionForm[key] || '0');
            parsedQuotas[key] = isNaN(val) || val <= 0 ? 0 : val;
        });

        const form: QuotaProfileCreate = {
            ...editForm,
            quotas: parsedQuotas,
            quota_type: 'nutrition',
        };

        setLoading(true);
        setError('');
        try {
            let saved: QuotaProfile;
            if (editMode === 'create') {
                saved = await createQuotaProfile(form);
            } else {
                saved = await updateQuotaProfile(selectedId!, form);
            }
            await loadProfiles();
            setSelectedId(saved.id);
            setEditMode('view');
            onSave?.(saved);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleDelete() {
        if (!selectedId) return;
        setLoading(true);
        setError('');
        try {
            await deleteQuotaProfile(selectedId);
            await loadProfiles();
            setSelectedId(profiles.length > 1 ? (profiles.find(p => p.id !== selectedId)?.id ?? null) : null);
            setEditMode('view');
            setConfirmDelete(false);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    async function handleDuplicate() {
        if (!selectedId) return;
        setLoading(true);
        setError('');
        try {
            const profile = profiles.find(p => p.id === selectedId)!;
            const newProfile = await duplicateQuotaProfile(selectedId, profile.name + ' (副本)');
            await loadProfiles();
            setSelectedId(newProfile.id);
            setEditMode('view');
            onSave?.(newProfile);
        } catch (e: any) {
            setError(e.message);
        } finally {
            setLoading(false);
        }
    }

    const selectedProfile = profiles.find(p => p.id === selectedId) ?? null;
    const isViewMode = editMode === 'view';
    const isEditMode = editMode === 'edit';
    const isCreateMode = editMode === 'create';
    const isSystemProfile = selectedProfile?.is_system ?? false;

    return (
        <>
            {/* 遮罩 */}
            <div className="fixed inset-0 bg-black/30 z-50" onClick={(e) => { e.stopPropagation(); onClose(); }} />

            {/* 弹窗 */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={(e) => { e.stopPropagation(); onClose(); }}>
                <div
                    className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden animate-slide-up"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* 头部 */}
                    <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-gradient-to-r from-primary-50 to-accent-50 flex-shrink-0">
                        <div>
                            <h2 className="text-base font-bold text-text-primary flex items-center gap-2">
                                <Settings size={16} className="text-primary-500" />
                                营养配额配置
                            </h2>
                            <p className="text-[11px] text-text-muted mt-0.5">
                                管理不同场景的营养标准，幼儿园/小学等均可配置
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="w-8 h-8 rounded-lg hover:bg-white/60 flex items-center justify-center"
                        >
                            <X size={16} className="text-text-secondary" />
                        </button>
                    </div>

                    <div className="flex flex-1 overflow-hidden">
                        {/* 左侧：配置文件列表 */}
                        <div className="w-52 border-r border-border-light flex flex-col flex-shrink-0">
                            <div className="px-3 py-2 border-b border-border-light flex items-center justify-between">
                                <span className="text-[10px] font-semibold text-text-muted uppercase">配置文件</span>
                                <button
                                    onClick={startCreate}
                                    className="w-5 h-5 rounded bg-primary-500 text-white flex items-center justify-center hover:bg-primary-600"
                                    title="新建配置"
                                >
                                    <Plus size={10} />
                                </button>
                            </div>
                            <div className="flex-1 overflow-y-auto">
                                {profiles.map(p => (
                                    <button
                                        key={p.id}
                                        onClick={() => selectProfile(p.id)}
                                        className={`w-full text-left px-3 py-2 text-xs border-b border-border-light/50 hover:bg-primary-50 transition-colors ${
                                            selectedId === p.id ? 'bg-primary-50 border-l-2 border-l-primary-500' : ''
                                        }`}
                                    >
                                        <div className="flex items-center gap-1">
                                            <span className="font-medium truncate">{p.name}</span>
                                            {p.is_system && (
                                                <span className="text-[8px] bg-gray-200 text-gray-500 px-1 rounded">内置</span>
                                            )}
                                        </div>
                                        <div className="text-[10px] text-text-muted truncate mt-0.5">{p.description || '无描述'}</div>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* 右侧：配置详情/编辑区 */}
                        <div className="flex-1 overflow-y-auto p-5">
                            {error && (
                                <div className="mb-4 px-3 py-2 bg-red-50 border border-red-200 rounded-lg text-xs text-red-600 flex items-center gap-2">
                                    <AlertTriangle size={12} />
                                    {error}
                                </div>
                            )}

                            {isViewMode && selectedProfile && (
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <h3 className="text-sm font-bold text-text-primary">{selectedProfile.name}</h3>
                                            <p className="text-[11px] text-text-muted mt-1">{selectedProfile.description || '无描述'}</p>
                                            <span className={`inline-block mt-1.5 text-[9px] px-1.5 py-0.5 rounded ${
                                                (selectedProfile as any).quota_type === 'nutrition'
                                                    ? 'bg-orange-100 text-orange-600'
                                                    : 'bg-green-100 text-green-600'
                                            }`}>
                                                {(selectedProfile as any).quota_type === 'nutrition' ? '营养素配额' : '未知类型'}
                                            </span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            {!isSystemProfile && (
                                                <>
                                                    <button
                                                        onClick={startEdit}
                                                        className="px-3 py-1.5 text-xs border border-border rounded-lg hover:bg-gray-50 flex items-center gap-1"
                                                    >
                                                        <Edit2 size={10} /> 编辑
                                                    </button>
                                                    <button
                                                        onClick={handleDuplicate}
                                                        className="px-3 py-1.5 text-xs border border-border rounded-lg hover:bg-gray-50 flex items-center gap-1"
                                                        title="复制"
                                                    >
                                                        <Copy size={10} />
                                                    </button>
                                                    <button
                                                        onClick={() => setConfirmDelete(true)}
                                                        className="px-3 py-1.5 text-xs border border-red-200 text-red-400 rounded-lg hover:bg-red-50 flex items-center gap-1"
                                                    >
                                                        <Trash2 size={10} /> 删除
                                                    </button>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {(selectedProfile as any).quota_type === 'nutrition' ? (
                                        <div className="grid grid-cols-2 gap-3">
                                            {NUTRITION_KEYS.map(({ key, label, unit, defaultVal }) => {
                                                const val = selectedProfile.quotas[key] ?? defaultVal;
                                                return (
                                                    <div key={key} className="bg-surface border border-border-light rounded-xl p-4">
                                                        <div className="text-[10px] text-text-muted mb-1">{label}</div>
                                                        <div className="text-lg font-bold text-text-primary">{val}</div>
                                                        <div className="text-[10px] text-text-muted mt-0.5">人均目标 / {unit}/人/天</div>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    ) : null}

                                    {confirmDelete && (
                                        <div className="flex items-center gap-3 p-3 bg-red-50 border border-red-200 rounded-xl">
                                            <AlertTriangle size={14} className="text-red-400 flex-shrink-0" />
                                            <div className="flex-1 text-xs text-red-600">
                                                确定删除配置文件「{selectedProfile.name}」？此操作不可恢复。
                                            </div>
                                            <button
                                                onClick={() => setConfirmDelete(false)}
                                                className="px-3 py-1 text-xs border border-border rounded-lg hover:bg-white"
                                            >
                                                取消
                                            </button>
                                            <button
                                                onClick={handleDelete}
                                                className="px-3 py-1 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600"
                                            >
                                                确认删除
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}

                            {(isCreateMode || isEditMode) && (
                                <div className="space-y-4">
                                    <div className="flex items-center gap-2 mb-2">
                                        <CheckCircle size={14} className="text-primary-500" />
                                        <span className="text-sm font-medium text-text-primary">
                                            {isCreateMode ? '新建配额配置' : '编辑配额配置'}
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="block text-[11px] text-text-muted mb-1">显示名称 *</label>
                                            <input
                                                type="text"
                                                value={editForm.name}
                                                onChange={e => setEditForm({ ...editForm, name: e.target.value })}
                                                className="w-full px-3 py-2 rounded-lg border border-border text-sm outline-none focus:border-primary-400"
                                                placeholder="如：幼儿园大班营养标准"
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-[11px] text-text-muted mb-1">内部标识符</label>
                                            <input
                                                type="text"
                                                value={editForm.class_type}
                                                onChange={e => setEditForm({ ...editForm, class_type: e.target.value })}
                                                className="w-full px-3 py-2 rounded-lg border border-border text-sm outline-none focus:border-primary-400"
                                                placeholder="如：kindergarten_class"
                                                disabled={isEditMode && isSystemProfile}
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-[11px] text-text-muted mb-1">描述说明</label>
                                        <input
                                            type="text"
                                            value={editForm.description}
                                            onChange={e => setEditForm({ ...editForm, description: e.target.value })}
                                            className="w-full px-3 py-2 rounded-lg border border-border text-sm outline-none focus:border-primary-400"
                                            placeholder="描述此配置的使用场景，如：适用于幼儿园大班学生每日营养摄入参考"
                                        />
                                    </div>

                                    <div>
                                        <label className="text-[11px] text-text-muted font-medium mb-2 block">
                                            营养素配额明细（人均每日目标）
                                        </label>
                                        <div className="grid grid-cols-2 gap-3">
                                            {NUTRITION_KEYS.map(({ key, label, unit, defaultVal }) => (
                                                <div key={key}>
                                                    <label className="block text-[10px] text-text-muted mb-1">{label}（{unit}/人/天）</label>
                                                    <input
                                                        type="number"
                                                        value={nutritionForm[key] ?? String(defaultVal)}
                                                        onChange={e => setNutritionForm({ ...nutritionForm, [key]: e.target.value })}
                                                        className="w-full px-3 py-2 rounded-lg border border-border-light text-sm outline-none focus:border-orange-300 text-right"
                                                        min={0}
                                                    />
                                                </div>
                                            ))}
                                        </div>
                                        <p className="text-[9px] text-text-muted mt-2">
                                            基于中国居民膳食营养素参考摄入量，适用于5-6岁幼儿园大班儿童参考标准。
                                        </p>
                                    </div>

                                    <div className="flex gap-3 pt-2">
                                        <button
                                            onClick={() => setEditMode('view')}
                                            className="flex-1 py-2.5 rounded-xl border border-border text-sm text-text-secondary hover:bg-gray-50"
                                        >
                                            取消
                                        </button>
                                        <button
                                            onClick={handleSave}
                                            disabled={loading || !editForm.name.trim()}
                                            className="flex-1 py-2.5 rounded-xl bg-gradient-to-r from-primary-500 to-primary-600 text-white text-sm font-medium flex items-center justify-center gap-1.5 hover:shadow-md disabled:opacity-50"
                                        >
                                            <Save size={14} />
                                            {loading ? '保存中...' : '保存配置'}
                                        </button>
                                    </div>
                                </div>
                            )}

                            {!selectedProfile && !isCreateMode && (
                                <div className="flex flex-col items-center justify-center h-full text-center text-text-muted">
                                    <Settings size={32} className="mb-3 opacity-30" />
                                    <p className="text-sm">从左侧选择一个配置文件查看</p>
                                    <button
                                        onClick={startCreate}
                                        className="mt-3 px-4 py-2 text-xs border border-dashed border-border rounded-lg hover:border-primary-300 hover:text-primary-500"
                                    >
                                        + 新建配置
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
}
