"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

import api from "@/lib/api";
import { Users, Copy, Plus, LogIn, UserMinus, Check } from "lucide-react";

interface FamilyMember {
  user_id: string;
  nickname: string;
  role: string;
  relation: string;
}

interface FamilyInfo {
  id: string;
  name: string;
  invite_code: string;
  member_count: number;
  members: FamilyMember[];
}

export default function FamilyPage() {
  const router = useRouter();

  const [family, setFamily] = useState<FamilyInfo | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [showJoin, setShowJoin] = useState(false);
  const [familyName, setFamilyName] = useState("");
  const [inviteCode, setInviteCode] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    api.get("/family/my").then(({ data }) => setFamily(data)).catch(() => {});
  }, []);

  const handleCreate = async () => {
    if (!familyName.trim()) return;
    try {
      const { data } = await api.post("/family/create", { name: familyName });
      setFamily(data);
      setShowCreate(false);
      setFamilyName("");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || "创建失败");
    }
  };

  const handleJoin = async () => {
    if (!inviteCode.trim()) return;
    try {
      const { data } = await api.post("/family/join", { invite_code: inviteCode });
      setFamily(data);
      setShowJoin(false);
      setInviteCode("");
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || "加入失败");
    }
  };

  const copyCode = () => {
    if (family?.invite_code) {
      navigator.clipboard.writeText(family.invite_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col  ">
      <header className="flex items-center justify-between">
        
        <h1 className="text-lg font-bold text-gray-900">家庭共享</h1>
      </header>

      <main className="flex-1 px-4 py-4 space-y-4 pb-20">
        {!family && (
          <div className="text-center py-10">
            <Users className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 mb-2">还没有加入家庭</p>
            <p className="text-xs text-gray-400 mb-6">创建家庭或通过邀请码加入，和家人一起管理饮食</p>
            <div className="flex gap-3 justify-center">
              <button onClick={() => setShowCreate(true)}
                className="flex items-center gap-2 px-5 py-3 bg-green-500 text-white rounded-xl font-medium hover:bg-green-600 transition-colors">
                <Plus className="w-4 h-4" /> 创建家庭
              </button>
              <button onClick={() => setShowJoin(true)}
                className="flex items-center gap-2 px-5 py-3 border border-green-500 text-green-600 rounded-xl font-medium hover:bg-green-50 transition-colors">
                <LogIn className="w-4 h-4" /> 加入家庭
              </button>
            </div>
          </div>
        )}

        {showCreate && (
          <div className="border border-green-200 rounded-xl p-4 bg-green-50 space-y-3">
            <h3 className="font-semibold text-green-800">创建家庭</h3>
            <input value={familyName} onChange={(e) => setFamilyName(e.target.value)}
              placeholder="家庭名称，如：小美和阿杰的家"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
            <div className="flex gap-2">
              <button onClick={() => setShowCreate(false)} className="flex-1 py-2 text-gray-600 border border-gray-200 rounded-lg text-sm">取消</button>
              <button onClick={handleCreate} className="flex-1 py-2 bg-green-500 text-white rounded-lg text-sm font-medium">创建</button>
            </div>
          </div>
        )}

        {showJoin && (
          <div className="border border-blue-200 rounded-xl p-4 bg-blue-50 space-y-3">
            <h3 className="font-semibold text-blue-800">加入家庭</h3>
            <input value={inviteCode} onChange={(e) => setInviteCode(e.target.value.toUpperCase())}
              placeholder="输入 6 位邀请码"
              maxLength={6}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm uppercase tracking-widest text-center" />
            <div className="flex gap-2">
              <button onClick={() => setShowJoin(false)} className="flex-1 py-2 text-gray-600 border border-gray-200 rounded-lg text-sm">取消</button>
              <button onClick={handleJoin} className="flex-1 py-2 bg-blue-500 text-white rounded-lg text-sm font-medium">加入</button>
            </div>
          </div>
        )}

        {family && (
          <>
            {/* Family Info */}
            <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
              <h2 className="font-bold text-purple-800 mb-1">{family.name}</h2>
              <p className="text-xs text-purple-600 mb-3">{family.member_count} 位成员</p>
              <div className="flex items-center gap-2">
                <span className="text-xs text-purple-500">邀请码：</span>
                <code className="text-sm font-mono font-bold text-purple-700 bg-white px-2 py-0.5 rounded">{family.invite_code}</code>
                <button onClick={copyCode} className="text-purple-500 hover:text-purple-700">
                  {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-[10px] text-purple-400 mt-2">分享邀请码给家人，即可加入家庭</p>
            </div>

            {/* Members */}
            <div>
              <h3 className="text-sm font-semibold text-gray-500 mb-2">家庭成员</h3>
              <div className="space-y-2">
                {family.members.map((m) => (
                  <div key={m.user_id} className="flex items-center justify-between border border-gray-100 rounded-xl px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-sm">👤</span>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{m.nickname}</p>
                        <p className="text-xs text-gray-400">{m.role === "owner" ? "创建者" : m.relation || "成员"}</p>
                      </div>
                    </div>
                    {m.role === "owner" && (
                      <span className="text-xs bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full">管理员</span>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Invite */}
            <button onClick={() => { navigator.clipboard.writeText(`我在用 MealMuse 管理饮食，邀请你加入我的家庭！邀请码：${family.invite_code}`); alert("已复制邀请信息"); }}
              className="w-full py-3 bg-purple-500 text-white rounded-xl font-medium hover:bg-purple-600 transition-colors flex items-center justify-center gap-2">
              <Plus className="w-4 h-4" /> 邀请家人
            </button>
          </>
        )}
      </main>
    </div>
  );
}
