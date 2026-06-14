import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "MealMuse - 每一餐，都是对自己的善待",
  description: "AI 驱动的智能饮食管理助手",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-[#fafafa]">{children}</body>
    </html>
  );
}
