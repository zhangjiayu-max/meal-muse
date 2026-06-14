"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import Sidebar from "@/components/sidebar";
import Topbar from "@/components/topbar";
import { ToastContainer } from "@/components/ui/toast";
import { ConfirmContainer } from "@/components/ui/confirm";

export default function MainLayout({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
    } else {
      setAuthenticated(true);
    }
    setMounted(true);
  }, [router]);

  if (!mounted || !authenticated) {
    return (
      <div className="flex h-screen bg-[#fafafa] items-center justify-center">
        <div className="text-gray-400">加载中...</div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Topbar />
        <main className="flex-1 overflow-auto bg-gray-50/50">
          <div className="max-w-6xl mx-auto p-6">
            <AnimatePresence mode="wait">
              <motion.div
                key={pathname}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2, ease: "easeInOut" }}
              >
                {children}
              </motion.div>
            </AnimatePresence>
          </div>
        </main>
      </div>
      <ToastContainer />
      <ConfirmContainer />
    </div>
  );
}
