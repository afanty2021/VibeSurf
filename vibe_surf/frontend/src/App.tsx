// -*- coding: utf-8 -*-
/**
 * VibeSurf前端应用主入口组件
 *
 * 这是VibeSurf Web应用的根组件，负责全局主题管理、路由配置
 * 和应用级别的状态初始化。集成React Router进行客户端路由，
 * 支持暗色/亮色主题切换，并提供加载状态处理。
 *
 * 主要功能：
 * - 全局主题状态管理
 * - React Router路由提供者
 * - 应用的Suspense边界处理
 * - 主题类名的DOM操作
 */

import "@xyflow/react/dist/style.css";
import { Suspense, useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { LoadingPage } from "./pages/LoadingPage";
import router from "./routes";
import { useDarkStore } from "./stores/darkStore";

/**
 * App应用主组件
 *
 * 作为整个应用的根组件，负责：
 * 1. 管理暗色/亮色主题切换
 * 2. 提供路由配置
 * 3. 处理应用级别的加载状态
 */
export default function App() {
  // 从Zustand状态管理中获取主题设置
  const dark = useDarkStore((state) => state.dark);

  /**
   * 主题切换副作用处理
   *
   * 监听主题状态变化，动态添加或移除DOM元素的dark类名，
   * 实现CSS变量的主题切换效果
   */
  useEffect(() => {
    if (!dark) {
      // 移除暗色主题类名
      document.getElementById("body")!.classList.remove("dark");
    } else {
      // 添加暗色主题类名
      document.getElementById("body")!.classList.add("dark");
    }
  }, [dark]);

  return (
    <Suspense fallback={<LoadingPage />}>
      <RouterProvider router={router} />
    </Suspense>
  );
}
