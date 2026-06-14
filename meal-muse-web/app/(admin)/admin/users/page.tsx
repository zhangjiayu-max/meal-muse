"use client";

import { useState, useEffect } from "react";
import api from "@/lib/api";
import {
  Users,
  Search,
  ChevronLeft,
  ChevronRight,
  User,
  Activity,
} from "lucide-react";

interface UserInfo {
  id: string;
  phone: string;
  nickname: string;
  height_cm: number | null;
  current_weight: number | null;
  target_weight: number | null;
  activity_level: string;
  daily_calorie_target: number | null;
  status: string;
  diet_record_count: number;
  last_login_at: string | null;
  created_at: string;
}

interface UsersResponse {
  total: number;
  page: number;
  page_size: number;
  users: UserInfo[];
}

export default function AdminUsersPage() {
  const [data, setData] = useState<UsersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

  useEffect(() => {
    loadUsers();
  }, [page]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/admin/users?page=${page}&page_size=20`);
      setData(data);
    } catch (err) {
      console.error("加载用户列表失败:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (userId: string, status: string) => {
    try {
      await api.put(`/admin/users/${userId}/status?status=${status}`);
      loadUsers();
    } catch (err) {
      alert("更新失败");
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return "未登录";
    return new Date(dateStr).toLocaleString("zh-CN");
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { label: string; color: string }> = {
      active: { label: "正常", color: "bg-green-100 text-green-700" },
      disabled: { label: "禁用", color: "bg-gray-100 text-gray-700" },
      banned: { label: "封禁", color: "bg-red-100 text-red-700" },
    };
    const info = statusMap[status] || { label: status, color: "bg-gray-100 text-gray-700" };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${info.color}`}>
        {info.label}
      </span>
    );
  };

  if (loading && !data) {
    return <div className="text-center py-10 text-gray-400">加载中...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">用户管理</h2>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索手机号/昵称"
              className="pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
            />
          </div>
          <button
            onClick={loadUsers}
            className="px-4 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600"
          >
            刷新
          </button>
        </div>
      </div>

      {/* 用户表格 */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  用户
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  手机号
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  身体数据
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  饮食记录
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  状态
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  最后登录
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  注册时间
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  操作
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
                        <User className="w-4 h-4 text-orange-600" />
                      </div>
                      <span className="font-medium text-gray-900">{user.nickname}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {user.phone}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {user.height_cm && user.current_weight
                      ? `${user.height_cm}cm / ${user.current_weight}kg`
                      : "未填写"}
                  </td>
                  <td className="px-4 py-3">
                    <span className="flex items-center gap-1 text-sm text-gray-600">
                      <Activity className="w-3 h-3" />
                      {user.diet_record_count} 条
                    </span>
                  </td>
                  <td className="px-4 py-3">{getStatusBadge(user.status)}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatDate(user.last_login_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={user.status}
                      onChange={(e) => handleStatusChange(user.id, e.target.value)}
                      className="text-sm border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-orange-500"
                    >
                      <option value="active">正常</option>
                      <option value="disabled">禁用</option>
                      <option value="banned">封禁</option>
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        {data && data.total > data.page_size && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <span className="text-sm text-gray-500">
              共 {data.total} 条，第 {data.page} 页
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={data.users.length < data.page_size}
                className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
