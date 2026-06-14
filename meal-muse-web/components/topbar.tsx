"use client";

import { Search, Bell, HelpCircle } from "lucide-react";

export default function Topbar() {
  return (
    <header className="flex items-center justify-between h-14 px-6 bg-white border-b border-gray-100 shrink-0">
      {/* Search */}
      <div className="flex items-center gap-2 bg-gray-50 rounded-lg px-3 py-1.5 w-80">
        <Search className="w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="搜索食物、食谱..."
          className="bg-transparent text-sm text-gray-700 placeholder-gray-400 focus:outline-none w-full"
        />
        <kbd className="text-[10px] text-gray-300 border border-gray-200 rounded px-1 py-0.5">⌘K</kbd>
      </div>

      {/* Right Actions */}
      <div className="flex items-center gap-2">
        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors">
          <HelpCircle className="w-5 h-5" />
        </button>
        <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-50 rounded-lg transition-colors relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
        </button>
      </div>
    </header>
  );
}
