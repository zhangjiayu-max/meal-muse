"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import {
  Database,
  RefreshCw,
  BookOpen,
  Tag,
  FileText,
} from "lucide-react";

interface KnowledgeStats {
  collections: Array<{
    name: string;
    count: number;
  }>;
  total_documents: number;
  message?: string;
}

interface KnowledgeCategories {
  categories: Array<{
    name: string;
    count: number;
  }>;
  sources: Array<{
    name: string;
    count: number;
  }>;
}

interface KnowledgeItem {
  id: string;
  content: string;
  metadata: Record<string, unknown>;
}

export default function AdminKnowledgePage() {
  const [stats, setStats] = useState<KnowledgeStats | null>(null);
  const [categories, setCategories] = useState<KnowledgeCategories | null>(null);
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    loadItems();
  }, [page]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, catsRes] = await Promise.all([
        api.get("/admin/knowledge/stats"),
        api.get("/admin/knowledge/categories"),
      ]);
      setStats(statsRes.data);
      setCategories(catsRes.data);
    } catch (err) {
      console.error("加载知识库统计失败:", err);
    } finally {
      setLoading(false);
    }
  };

  const loadItems = async () => {
    try {
      const { data } = await api.get(`/admin/knowledge/list?page=${page}&page_size=20`);
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error("加载知识库列表失败:", err);
    }
  };

  if (loading) {
    return <div className="text-center py-10 text-gray-400">加载中...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">知识库管理</h2>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {/* 统计概览 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Database className="w-5 h-5 text-blue-600" />
            </div>
            <span className="text-sm text-gray-500">向量集合</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {stats?.collections.length || 0}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-green-100 p-2 rounded-lg">
              <FileText className="w-5 h-5 text-green-600" />
            </div>
            <span className="text-sm text-gray-500">总文档数</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {stats?.total_documents || 0}
          </p>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="flex items-center gap-3 mb-2">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Tag className="w-5 h-5 text-purple-600" />
            </div>
            <span className="text-sm text-gray-500">知识分类</span>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {categories?.categories.length || 0}
          </p>
        </div>
      </div>

      {/* 提示信息 */}
      {stats?.message && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
          <p className="text-sm text-yellow-700">{stats.message}</p>
        </div>
      )}

      {/* 分类统计 */}
      {categories && categories.categories && categories.categories.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Tag className="w-5 h-5" />
            分类统计
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {categories.categories.map((cat) => (
              <div
                key={cat.name}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <span className="text-sm text-gray-700">{cat.name}</span>
                <span className="text-sm font-medium text-orange-600">{cat.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 来源统计 */}
      {categories && categories.sources && categories.sources.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <BookOpen className="w-5 h-5" />
            来源统计
          </h3>
          <div className="space-y-2">
            {categories.sources.map((source) => (
              <div
                key={source.name}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <span className="text-sm text-gray-700">{source.name}</span>
                <span className="text-sm font-medium text-blue-600">{source.count} 条</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 知识列表 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">知识条目</h3>
        </div>

        {items.length === 0 ? (
          <div className="text-center py-10 text-gray-400">
            暂无知识条目，请先运行蒸馏脚本导入知识
          </div>
        ) : (
          <div className="divide-y divide-gray-100">
            {items.map((item) => (
              <div key={item.id} className="px-5 py-4 hover:bg-gray-50">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-xs text-gray-400 font-mono">{item.id}</span>
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                    {(item.metadata as Record<string, string>)?.category || "未分类"}
                  </span>
                </div>
                <p className="text-sm text-gray-700">{item.content}</p>
                {(item.metadata as Record<string, string>)?.source && (
                  <p className="text-xs text-gray-400 mt-2">
                    来源：{(item.metadata as Record<string, string>)?.source}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 分页 */}
        {total > 20 && (
          <div className="flex items-center justify-between px-5 py-3 border-t border-gray-200">
            <span className="text-sm text-gray-500">共 {total} 条</span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-3 py-1 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                上一页
              </button>
              <span className="text-sm text-gray-600">第 {page} 页</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={items.length < 20}
                className="px-3 py-1 text-sm border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 使用说明 */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-5">
        <h4 className="font-semibold text-blue-900 mb-2">📚 知识库使用说明</h4>
        <div className="text-sm text-blue-700 space-y-2">
          <p>1. 运行蒸馏脚本导入知识：</p>
          <code className="block bg-blue-100 px-3 py-2 rounded text-xs">
            cd meal-muse-api && python scripts/distill.py full /path/to/book.pdf --name 书名
          </code>
          <p>2. 查看已蒸馏书籍列表：</p>
          <code className="block bg-blue-100 px-3 py-2 rounded text-xs">
            python scripts/distill.py list
          </code>
          <p>3. 重建向量索引：</p>
          <code className="block bg-blue-100 px-3 py-2 rounded text-xs">
            python scripts/distill.py reindex
          </code>
        </div>
      </div>
    </div>
  );
}
