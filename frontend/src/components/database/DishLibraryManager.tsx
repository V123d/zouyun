import { useState, useEffect, useMemo } from 'react';
import {
    Search, Plus, Edit2, Trash2, X, Save,
    Filter, Info, Utensils, Flame
} from 'lucide-react';
import {
    getDishLibrary, getDishCategories,
    createDish, updateDish, deleteDish, addCategory
} from '../../services/api';
import type { DishInfo } from '../../types';

export default function DishLibraryManager() {
    const [dishes, setDishes] = useState<DishInfo[]>([]);
    const [categories, setCategories] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string>('全部');

    // 新增分类相关状态
    const [newDishCategory, setNewDishCategory] = useState('');
    const [isAddingDishCategory, setIsAddingDishCategory] = useState(false);

    // 编辑相关状态
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingDish, setEditingDish] = useState<Partial<DishInfo> | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [dishData, catData] = await Promise.all([
                getDishLibrary(),
                getDishCategories()
            ]);
            setDishes(dishData);
            setCategories(['全部', ...catData]);
        } catch (error) {
            console.error('Failed to fetch dishes:', error);
        } finally {
            setLoading(false);
        }
    };

    // 添加新的菜品分类
    const handleAddDishCategory = async () => {
        const trimmed = newDishCategory.trim();
        if (!trimmed) return;
        const success = await addCategory('dish', trimmed);
        if (success) {
            setCategories(prev => {
                const filtered = prev.filter(c => c !== '全部');
                return [...filtered, trimmed].sort((a, b) => a.localeCompare(b, 'zh-CN'));
            });
            if (editingDish) {
                setEditingDish({ ...editingDish, category: trimmed });
            }
        }
        setNewDishCategory('');
        setIsAddingDishCategory(false);
    };

    const filteredDishes = useMemo(() => {
        return dishes.filter((dish: DishInfo) => {
            const matchesSearch = dish.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                dish.id.toString().includes(searchQuery);
            const matchesCategory = selectedCategory === '全部' || dish.category === selectedCategory;
            return matchesSearch && matchesCategory;
        });
    }, [dishes, searchQuery, selectedCategory]);

    const handleAdd = () => {
        setEditingDish({
            name: '',
            category: categories[1] || '主食',
            ingredients_quantified: [],
            applicable_meals: ['午餐', '晚餐'],
            flavor: '咸鲜',
            cost_per_serving: 0,
            nutrition: { calories: 0, protein: 0, carbs: 0, fat: 0 },
            tags: []
        });
        setIsModalOpen(true);
    };

    const handleEdit = (dish: DishInfo) => {
        setEditingDish({ ...dish });
        setIsModalOpen(true);
    };

    const handleDelete = async (id: number) => {
        if (!window.confirm('确定要删除这个菜品吗？此操作不可撤销。')) return;
        try {
            await deleteDish(id);
            setDishes(dishes.filter((d: DishInfo) => d.id !== id));
        } catch (error) {
            alert('删除失败');
        }
    };

    const handleSave = async () => {
        if (!editingDish || !editingDish.name) return;
        setIsSaving(true);
        try {
            if (editingDish.id) {
                const updated = await updateDish(editingDish.id, editingDish);
                setDishes(dishes.map((d: DishInfo) => d.id === updated.id ? updated : d));
            } else {
                const created = await createDish(editingDish);
                setDishes([created, ...dishes]);
            }
            setIsModalOpen(false);
        } catch (error) {
            alert('保存失败');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* 工具栏 */}
            <div className="p-4 border-b border-border-light flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3 flex-1 min-w-[300px]">
                    <div className="relative flex-1 max-w-sm">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" size={16} />
                        <input
                            type="text"
                            placeholder="搜索菜品名称或 ID..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-surface border border-border rounded-xl text-sm focus:border-primary-400 outline-none transition-all"
                        />
                    </div>
                    <div className="flex items-center gap-2">
                        <Filter size={14} className="text-text-muted" />
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="bg-surface border border-border rounded-xl px-3 py-2 text-sm outline-none focus:border-primary-400"
                        >
                            {categories.map((cat: string) => (
                                <option key={cat} value={cat}>{cat}</option>
                            ))}
                        </select>
                    </div>
                </div>
                <button
                    onClick={handleAdd}
                    className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-xl text-sm font-medium hover:bg-primary-700 shadow-sm transition-all active:scale-95"
                >
                    <Plus size={16} />
                    新增菜品
                </button>
            </div>

            {/* 表格区域 */}
            <div className="flex-1 overflow-auto">
                {loading ? (
                    <div className="flex flex-col items-center justify-center h-64 text-text-muted gap-3">
                        <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin" />
                        <span className="text-sm">加载菜品库中...</span>
                    </div>
                ) : filteredDishes.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-64 text-text-muted">
                        <Utensils size={48} className="mb-3 opacity-20" />
                        <span className="text-sm">暂无符合条件的菜品</span>
                    </div>
                ) : (
                    <table className="w-full border-collapse text-left">
                        <thead className="sticky top-0 bg-gray-50 z-10">
                            <tr className="border-b border-border-light">
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider w-16 text-center">ID</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">菜品名称</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">分类</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">口味</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">单份成本</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">配料组成</th>
                                <th className="px-6 py-4 text-xs font-bold text-text-muted uppercase tracking-wider">操作</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-light">
                            {filteredDishes.map((dish) => (
                                <tr key={dish.id} className="hover:bg-primary-50/30 transition-colors group">
                                    <td className="px-6 py-4 text-sm text-text-muted text-center font-mono">{dish.id}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-sm font-bold text-text-primary group-hover:text-primary-700 transition-colors">{dish.name}</span>
                                            <div className="flex flex-wrap gap-1 mt-1">
                                                {dish.tags.slice(0, 3).map((tag: string, i: number) => (
                                                    <span key={i} className="px-1.5 py-0.5 bg-gray-100 text-[10px] text-text-muted rounded capitalize">#{tag}</span>
                                                ))}
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="px-2.5 py-1 bg-accent-50 text-accent-700 text-xs font-medium rounded-full border border-accent-100">
                                            {dish.category}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-text-secondary">{dish.flavor}</td>
                                    <td className="px-6 py-4 text-sm font-semibold text-warm-600">¥{dish.cost_per_serving.toFixed(2)}</td>
                                    <td className="px-6 py-4">
                                        <div className="flex flex-wrap gap-1.5 max-w-[240px]">
                                            {dish.ingredients_quantified.map((ing: any, i: number) => (
                                                <div key={i} className="flex items-center gap-0.5 px-1.5 py-0.5 bg-primary-50 text-primary-700 rounded text-[10px] whitespace-nowrap">
                                                    <span>{ing.name}</span>
                                                    <span className="opacity-50">{ing.amount_g}g</span>
                                                </div>
                                            ))}
                                            {dish.ingredients_quantified.length === 0 && <span className="text-[10px] text-text-muted italic">未录入</span>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => handleEdit(dish)}
                                                className="p-1.5 text-blue-500 hover:bg-blue-50 rounded-lg transition-colors"
                                                title="编辑"
                                            >
                                                <Edit2 size={16} />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(dish.id)}
                                                className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                title="删除"
                                            >
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* 编辑/新增弹窗 */}
            {isModalOpen && editingDish && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                    <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setIsModalOpen(false)} />
                    <div className="relative bg-white w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                        {/* 弹窗头部 */}
                        <div className="px-6 py-4 border-b border-border-light flex items-center justify-between bg-gradient-to-r from-primary-50/50 to-transparent">
                            <h3 className="text-lg font-bold text-text-primary flex items-center gap-2">
                                {editingDish.id ? <Edit2 size={18} className="text-primary-500" /> : <Plus size={20} className="text-primary-500" />}
                                {editingDish.id ? '编辑菜品' : '新增菜品'}
                            </h3>
                            <button onClick={() => setIsModalOpen(false)} className="p-2 hover:bg-gray-100 rounded-full transition-colors">
                                <X size={20} className="text-text-muted" />
                            </button>
                        </div>

                        {/* 弹窗内容 */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {/* 基础信息 */}
                            <div className="grid grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-xs font-bold text-text-muted uppercase mb-1.5">菜品名称</label>
                                    <input
                                        type="text"
                                        value={editingDish.name}
                                        onChange={(e) => setEditingDish({ ...editingDish, name: e.target.value })}
                                        className="w-full px-4 py-2.5 rounded-xl border border-border text-sm focus:border-primary-400 outline-none transition-all"
                                        placeholder="如：红烧肉"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-text-muted uppercase mb-1.5">所属分类</label>
                                    {!isAddingDishCategory ? (
                                        <div className="flex gap-1">
                                            <select
                                                value={editingDish.category}
                                                onChange={(e) => setEditingDish({ ...editingDish, category: e.target.value })}
                                                className="flex-1 px-4 py-2.5 rounded-xl border border-border text-sm focus:border-primary-400 outline-none transition-all"
                                            >
                                                {categories.filter((c: string) => c !== '全部').map((cat: string) => (
                                                    <option key={cat} value={cat}>{cat}</option>
                                                ))}
                                            </select>
                                            <button
                                                onClick={() => setIsAddingDishCategory(true)}
                                                className="px-3 py-2 bg-primary-50 border border-primary-200 rounded-xl text-primary-600 hover:bg-primary-100 text-sm"
                                                title="添加新分类"
                                            >
                                                <Plus size={14} />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex gap-1">
                                            <input
                                                type="text"
                                                autoFocus
                                                value={newDishCategory}
                                                onChange={(e) => setNewDishCategory(e.target.value)}
                                                onKeyDown={(e) => {
                                                    if (e.key === 'Enter') handleAddDishCategory();
                                                    if (e.key === 'Escape') { setIsAddingDishCategory(false); setNewDishCategory(''); }
                                                }}
                                                placeholder="输入新分类名称"
                                                className="flex-1 px-3 py-2 rounded-xl border border-accent-300 text-sm focus:border-primary-400 outline-none"
                                            />
                                            <button
                                                onClick={handleAddDishCategory}
                                                className="px-3 py-2 bg-primary-600 text-white rounded-xl hover:bg-primary-700 text-sm"
                                            >
                                                <Save size={14} />
                                            </button>
                                            <button
                                                onClick={() => { setIsAddingDishCategory(false); setNewDishCategory(''); }}
                                                className="px-3 py-2 bg-gray-100 text-text-muted rounded-xl hover:bg-gray-200 text-sm"
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    )}
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-text-muted uppercase mb-1.5">口味</label>
                                    <input
                                        type="text"
                                        value={editingDish.flavor}
                                        onChange={(e) => setEditingDish({ ...editingDish, flavor: e.target.value })}
                                        className="w-full px-4 py-2.5 rounded-xl border border-border text-sm focus:border-primary-400 outline-none transition-all"
                                        placeholder="如：咸鲜、微辣"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-text-muted uppercase mb-1.5">单份成本 (元)</label>
                                    <input
                                        type="number"
                                        value={editingDish.cost_per_serving}
                                        onChange={(e) => setEditingDish({ ...editingDish, cost_per_serving: Number(e.target.value) })}
                                        className="w-full px-4 py-2.5 rounded-xl border border-border text-sm focus:border-primary-400 outline-none transition-all"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-text-muted uppercase mb-1.5">适用餐次</label>
                                    <div className="flex flex-wrap gap-2 mt-1">
                                        {['早餐', '午餐', '晚餐', '夜宵'].map((meal: string) => (
                                            <button
                                                key={meal}
                                                onClick={() => {
                                                    const current = editingDish.applicable_meals || [];
                                                    const next = current.includes(meal)
                                                        ? current.filter((m: string) => m !== meal)
                                                        : [...current, meal];
                                                    setEditingDish({ ...editingDish, applicable_meals: next });
                                                }}
                                                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                                                    editingDish.applicable_meals?.includes(meal)
                                                        ? 'bg-primary-500 text-white border-primary-500'
                                                        : 'bg-white text-text-secondary border-border hover:border-primary-300'
                                                }`}
                                            >
                                                {meal}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* 食材量化 */}
                            <div>
                                <h4 className="text-xs font-bold text-text-muted uppercase mb-3 flex items-center justify-between">
                                    <div className="flex items-center gap-1.5">
                                        <Flame size={14} className="text-primary-400" />
                                        量化食材列表
                                    </div>
                                    <button
                                        onClick={() => {
                                            const current = editingDish.ingredients_quantified || [];
                                            setEditingDish({
                                                ...editingDish,
                                                ingredients_quantified: [...current, { name: '', amount_g: 50 }]
                                            });
                                        }}
                                        className="text-[10px] text-primary-600 hover:text-primary-700 font-bold flex items-center gap-0.5"
                                    >
                                        <Plus size={10} /> 添加食材
                                    </button>
                                </h4>
                                <div className="space-y-2">
                                    {editingDish.ingredients_quantified?.map((ing: any, i: number) => (
                                        <div key={i} className="flex items-center gap-2 group">
                                            <input
                                                type="text"
                                                value={ing.name}
                                                onChange={(e) => {
                                                    const next = [...editingDish.ingredients_quantified!];
                                                    next[i] = { ...next[i], name: e.target.value };
                                                    setEditingDish({ ...editingDish, ingredients_quantified: next });
                                                }}
                                                placeholder="食材名"
                                                className="flex-1 px-3 py-1.5 rounded-lg border border-border text-xs focus:border-primary-400 outline-none"
                                            />
                                            <input
                                                type="number"
                                                value={ing.amount_g}
                                                onChange={(e) => {
                                                    const next = [...editingDish.ingredients_quantified!];
                                                    next[i] = { ...next[i], amount_g: Number(e.target.value) };
                                                    setEditingDish({ ...editingDish, ingredients_quantified: next });
                                                }}
                                                className="w-20 px-3 py-1.5 rounded-lg border border-border text-xs text-center outline-none"
                                            />
                                            <span className="text-[10px] text-text-muted w-4">g</span>
                                            <button
                                                onClick={() => {
                                                    const next = editingDish.ingredients_quantified!.filter((_: any, idx: number) => idx !== i);
                                                    setEditingDish({ ...editingDish, ingredients_quantified: next });
                                                }}
                                                className="p-1.5 text-red-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    ))}
                                    {editingDish.ingredients_quantified?.length === 0 && (
                                        <div className="text-center py-4 bg-gray-50 rounded-xl border border-dashed border-gray-200">
                                            <span className="text-[10px] text-text-muted">点击"添加食材"开始录入配方数据</span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* 营养素信息 */}
                            <div>
                                <h4 className="text-xs font-bold text-text-muted uppercase mb-3 flex items-center gap-1.5">
                                    <Flame size={14} className="text-orange-400" />
                                    营养素信息（每份）
                                </h4>
                                <div className="grid grid-cols-4 gap-3">
                                    <div>
                                        <label className="block text-[10px] text-text-muted mb-1">热量 (kcal)</label>
                                        <input
                                            type="number"
                                            value={editingDish.nutrition?.calories ?? 0}
                                            onChange={(e) => setEditingDish({
                                                ...editingDish,
                                                nutrition: { ...editingDish.nutrition!, calories: Number(e.target.value) }
                                            })}
                                            className="w-full px-3 py-1.5 rounded-lg border border-border text-xs text-center focus:border-primary-400 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] text-text-muted mb-1">蛋白质 (g)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={editingDish.nutrition?.protein ?? 0}
                                            onChange={(e) => setEditingDish({
                                                ...editingDish,
                                                nutrition: { ...editingDish.nutrition!, protein: Number(e.target.value) }
                                            })}
                                            className="w-full px-3 py-1.5 rounded-lg border border-border text-xs text-center focus:border-primary-400 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] text-text-muted mb-1">碳水化合物 (g)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={editingDish.nutrition?.carbs ?? 0}
                                            onChange={(e) => setEditingDish({
                                                ...editingDish,
                                                nutrition: { ...editingDish.nutrition!, carbs: Number(e.target.value) }
                                            })}
                                            className="w-full px-3 py-1.5 rounded-lg border border-border text-xs text-center focus:border-primary-400 outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-[10px] text-text-muted mb-1">脂肪 (g)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={editingDish.nutrition?.fat ?? 0}
                                            onChange={(e) => setEditingDish({
                                                ...editingDish,
                                                nutrition: { ...editingDish.nutrition!, fat: Number(e.target.value) }
                                            })}
                                            className="w-full px-3 py-1.5 rounded-lg border border-border text-xs text-center focus:border-primary-400 outline-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* 弹窗底部 */}
                        <div className="px-6 py-4 border-t border-border-light bg-gray-50 flex items-center justify-between">
                            <div className="flex items-center gap-1.5 text-[10px] text-text-muted">
                                <Info size={12} />
                                所有字段均为必填，量化单位统一为"克 (g)"
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setIsModalOpen(false)}
                                    className="px-6 py-2 rounded-xl text-sm font-medium text-text-secondary hover:bg-white transition-all"
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleSave}
                                    disabled={isSaving || !editingDish.name}
                                    className="px-6 py-2 rounded-xl bg-primary-600 text-white text-sm font-bold flex items-center gap-2 hover:bg-primary-700 shadow-lg shadow-primary-200 transition-all disabled:opacity-50 disabled:shadow-none"
                                >
                                    {isSaving ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> : <Save size={16} />}
                                    保存菜品
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
