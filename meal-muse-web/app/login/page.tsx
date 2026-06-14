"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { Leaf, Phone, Key, Zap } from "lucide-react";
import type { TokenResponse } from "@/types";

// 判断是否为开发环境
const isDev = process.env.NODE_ENV === "development";

export default function LoginPage() {
  const router = useRouter();

  // 已登录则直接跳首页
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      window.location.href = "/";
    }
  }, []);
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDevAutoLogin = async () => {
    setLoading(true);
    try {
      const { data } = await api.post<TokenResponse>("/auth/dev-auto-login");
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      window.location.href = "/";
    } catch {
      // 自动登录失败不影响手动登录
      console.log("自动登录失败，请手动登录");
    } finally {
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    if (!phone || phone.length !== 11) {
      setError("请输入正确的手机号");
      return;
    }
    try {
      await api.post("/auth/send-code", { phone });
      setError("");
      alert("验证码已发送（开发环境固定：888888）");
    } catch {
      setError("发送验证码失败");
    }
  };

  const handleLogin = async () => {
    if (!phone || !code) {
      setError("请填写手机号和验证码");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post<TokenResponse>("/auth/login", { phone, code });
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("user", JSON.stringify(data.user));
      // 强制刷新页面，避免状态不同步
      window.location.href = "/";
    } catch (err: unknown) {
      const apiErr = err as { response?: { data?: { detail?: string } } };
      setError(apiErr.response?.data?.detail || "登录失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-white">
      {/* Logo */}
      <div className="flex flex-col items-center mb-10">
        <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mb-4">
          <Leaf className="w-8 h-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">MealMuse</h1>
        <p className="text-sm text-gray-500 mt-1">每一餐，都是对自己的善待</p>
      </div>

      {/* Form */}
      <div className="w-full max-w-sm space-y-4">
        {/* Phone */}
        <div className="relative">
          <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="手机号"
            maxLength={11}
            className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
          />
        </div>

        {/* Code */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="验证码"
              maxLength={6}
              className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={handleSendCode}
            className="px-4 py-3 text-sm font-medium text-green-600 bg-green-50 rounded-lg hover:bg-green-100 transition-colors whitespace-nowrap"
          >
            获取验证码
          </button>
        </div>

        {/* 开发环境提示 */}
        {isDev && (
          <p className="text-xs text-gray-400 text-center">
            开发环境验证码固定为 <span className="font-mono text-green-500">888888</span>
          </p>
        )}

        {/* Error */}
        {error && (
          <p className="text-sm text-red-500 text-center">{error}</p>
        )}

        {/* Login Button */}
        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
        >
          {loading ? "登录中..." : "登 录"}
        </button>

        {/* Dev Auto Login */}
        {isDev && (
          <button
            onClick={handleDevAutoLogin}
            disabled={loading}
            className="w-full py-3 bg-orange-500 text-white font-semibold rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <Zap className="w-4 h-4" />
            开发环境一键登录
          </button>
        )}

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-200" />
          <span className="text-xs text-gray-400">或</span>
          <div className="flex-1 h-px bg-gray-200" />
        </div>

        {/* WeChat Login (即将上线) */}
        <button
          disabled
          className="w-full py-3 bg-gray-100 text-gray-400 font-semibold rounded-lg cursor-not-allowed flex items-center justify-center gap-2"
        >
          <span className="text-lg">💬</span>
          微信登录（即将上线）
        </button>

        <p className="text-[10px] text-gray-400 text-center mt-4">
          登录即表示同意《用户协议》和《隐私政策》
        </p>
      </div>
    </div>
  );
}
