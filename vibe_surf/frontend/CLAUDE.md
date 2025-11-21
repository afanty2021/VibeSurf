[根目录](../../../CLAUDE.md) > [vibe_surf](../) > **frontend**

# React前端界面模块 (frontend)

## 模块职责

React前端界面模块是VibeSurf的Web用户界面，基于React + TypeScript构建，提供直观的流程编排、任务监控、配置管理等功能。集成了React Flow用于可视化工作流编辑，Zustand用于状态管理，Chakra UI用于组件库。

## 入口与启动

### 主要入口文件
- **src/App.tsx** - React应用主入口，包含路由和全局状态初始化
- **package.json** - 项目依赖和构建脚本配置
- **index.html** - HTML模板文件

### 启动流程
1. 加载HTML模板和基础样式
2. 初始化React应用和全局状态
3. 配置路由和权限守卫
4. 加载用户设置和主题配置
5. 初始化API客户端和WebSocket连接

### 开发命令
```bash
# 安装依赖
npm install

# 开发模式启动
npm run dev

# 构建生产版本
npm run build

# 类型检查
npm run type-check
```

## 对外接口

### API客户端结构 (src/controllers/API/)
- **index.ts** - API客户端主入口，统一管理所有API调用
- **queries/auth/** - 认证相关API（登录、用户管理、权限验证）
- **queries/flows/** - 工作流相关API（创建、编辑、执行、导入导出）
- **queries/files/** - 文件管理API（上传、下载、列表、删除）
- **queries/folders/** - 文件夹管理API（创建、组织、权限管理）
- **queries/config/** - 配置管理API（LLM配置、系统设置）
- **queries/_builds/** - 构建管理API（组件构建、状态监控）

### 核心API调用示例
```typescript
// 认证相关
const { data: user } = useGetUserQuery();
const loginUser = usePostLoginUserMutation();

// 工作流管理
const { data: flows } = useGetFlowsQuery();
const createFlow = usePostAddFlowMutation();
const updateFlow = usePatchUpdateFlowMutation();

// 文件操作
const uploadFile = usePostUploadFileMutation();
const { data: files } = useGetFilesQuery();
```

### WebSocket连接
- **实时任务状态更新** - 任务执行进度、代理状态变化
- **实时通知系统** - 错误提示、完成通知、系统消息
- **协作功能** - 多用户实时编辑（未来扩展）

## 关键依赖与配置

### 核心依赖
- **React 18** - 主框架，支持并发特性
- **TypeScript** - 类型安全
- **React Router DOM** - 客户端路由
- **React Flow** - 流程图可视化编辑器
- **Zustand** - 轻量级状态管理
- **Chakra UI** - 组件库
- **TanStack Query** - 服务端状态管理和缓存
- **React Hook Form** - 表单管理

### 开发依赖
- **Vite** - 构建工具
- **ESLint + Prettier** - 代码质量保证
- **Vitest** - 单元测试框架
- **Playwright** - E2E测试框架

### 环境配置
```typescript
// src/config/environment.ts
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9335';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:9335';
export const ENABLE_TELEMETRY = import.meta.env.VITE_ENABLE_TELEMETRY !== 'false';
```

## 数据模型

### 前端状态管理

#### FlowStore (工作流状态)
```typescript
interface FlowState {
  currentFlow: Flow | null;
  flows: Flow[];
  folders: Folder[];
  selectedComponents: string[];
  copiedComponents: ComponentData[];
  viewport: Viewport;
  // 状态更新方法
  setCurrentFlow: (flow: Flow) => void;
  addFlow: (flow: Flow) => void;
  updateFlow: (id: string, updates: Partial<Flow>) => void;
  deleteFlow: (id: string) => void;
}
```

#### ChatStore (聊天状态)
```typescript
interface ChatState {
  messages: Message[];
  input: string;
  isLoading: boolean;
  sessionId: string | null;
  // 聊天方法
  addMessage: (message: Message) => void;
  setInput: (input: string) => void;
  clearMessages: () => void;
}
```

### 数据类型定义
```typescript
// 工作流相关
interface Flow {
  id: string;
  name: string;
  description?: string;
  data: GraphData;
  folder_id?: string;
  locked: boolean;
  created_at: string;
  updated_at: string;
}

// 组件相关
interface ComponentData {
  id: string;
  type: string;
  display_name: string;
  data: Record<string, any>;
  position: { x: number; y: number };
}

// 任务相关
interface Task {
  task_id: string;
  session_id: string;
  task_description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}
```

## 核心组件架构

### 布局组件 (src/components/core/)
- **AppHeaderComponent** - 顶部导航栏，包含Logo、用户菜单、通知
- **CanvasControlsComponent** - 画布控制面板（缩放、居中、布局）
- **SidePanelComponent** - 侧边栏组件（组件库、属性面板）
- **StatusBarComponent** - 状态栏显示（连接状态、任务状态）

### 编辑器组件 (src/components/editor/)
- **FlowEditor** - 主要的流程编辑器
- **CustomNodes** - 自定义节点组件库
- **PropertyPanel** - 属性编辑面板
- **ComponentPalette** - 组件选择面板

### 通用组件 (src/components/common/)
- **LoadingComponent** - 加载状态指示器
- **ErrorBoundary** - 错误边界组件
- **ModalComponent** - 通用对话框
- **TooltipComponent** - 工具提示组件

### 自定义节点系统

#### 节点类型
- **GenericNode** - 通用节点组件，支持各种类型的数据节点
- **NoteNode** - 便签节点，用于添加注释
- **ChatNode** - 聊天节点，集成对话功能
- **ToolNode** - 工具节点，调用外部工具

#### 节点生命周期
```typescript
interface NodeLifecycle {
  onMount: () => void;
  onUpdate: (updates: NodeData) => void;
  onValidate: () => ValidationResult;
  onDestroy: () => void;
  onError: (error: Error) => void;
}
```

## 路由和权限

### 路由结构
```typescript
// src/router/index.tsx
const routes = [
  { path: '/', element: <HomePage /> },
  { path: '/chat', element: <ChatPage /> },
  { path: '/flows', element: <FlowsPage /> },
  { path: '/flows/:id', element: <FlowEditorPage /> },
  { path: '/settings', element: <SettingsPage />,
    guard: 'authSettings' },
  { path: '/admin', element: <AdminPage />,
    guard: 'authAdmin' },
];
```

### 权限守卫
- **AuthGuard** - 基础认证守卫
- **AdminGuard** - 管理员权限守卫
- **SettingsGuard** - 设置页面权限守卫
- **LoginGuard** - 登录状态守卫

## 测试与质量

### 测试策略
- **单元测试** - 使用Vitest测试组件逻辑和工具函数
- **集成测试** - 测试组件间交互和API调用
- **E2E测试** - 使用Playwright测试用户完整流程

### 测试覆盖领域
- 组件渲染测试
- 用户交互测试
- API集成测试
- 路由导航测试
- 状态管理测试

### 代码质量保证
- **TypeScript严格模式** - 确保类型安全
- **ESLint规则** - 代码规范检查
- **Prettier格式化** - 统一代码风格
- **Husky钩子** - Git提交前检查

## 性能优化

### 组件优化
- **React.memo** - 防止不必要的重渲染
- **useMemo/useCallback** - 缓存计算结果和函数引用
- **虚拟化** - 大列表虚拟滚动
- **代码分割** - 路由级别的懒加载

### 状态管理优化
- **选择性订阅** - Zustand状态选择器
- **数据缓存** - TanStack Query缓存策略
- **乐观更新** - 提升用户体验的即时反馈

### 构建优化
- **Tree shaking** - 移除未使用代码
- **代码压缩** - 生产环境代码压缩
- **资源优化** - 图片压缩和CDN使用

## 国际化支持

### 多语言配置
- **i18n配置** - react-i18next集成
- **语言包** - 支持中文、英文
- **动态切换** - 运行时语言切换

### 本地化内容
- 界面文本本地化
- 日期时间格式化
- 数字格式化
- 错误消息本地化

## 主题系统

### 主题配置
- **Light/Dark模式** - 支持明暗主题切换
- **主题变量** - CSS自定义属性
- **动态切换** - 运行时主题切换
- **持久化** - 用户主题偏好保存

### 主题定制
- **颜色系统** - 基于设计令牌的颜色管理
- **组件主题** - 组件级别的主题定制
- **品牌定制** - 企业品牌颜色集成

## 常见问题 (FAQ)

### Q: 如何添加新的自定义节点类型？
A: 在CustomNodes目录下创建新组件，实现NodeInterface接口，然后在节点注册表中注册。

### Q: 如何处理大规模流程图的性能问题？
A: 使用React Flow的虚拟化、节点分组、懒加载等技术，避免一次渲染过多节点。

### Q: 如何集成新的外部API？
A: 在API控制器中添加新的查询和变更，使用TanStack Query管理数据状态。

### Q: 如何进行单元测试？
A: 使用Vitest + React Testing Library，遵循"测试用户行为"原则编写测试。

## 相关文件清单

### 应用入口
- `src/App.tsx` - React应用主入口
- `src/main.tsx` - 应用渲染入口
- `index.html` - HTML模板

### 路由和页面
- `src/router/` - 路由配置
- `src/pages/` - 页面组件
- `src/components/` - 可复用组件

### 状态管理
- `src/stores/` - Zustand状态存储
- `src/hooks/` - 自定义React Hooks

### API和数据
- `src/controllers/API/` - API调用封装
- `src/types/` - TypeScript类型定义

### 样式和主题
- `src/theme/` - 主题配置
- `src/styles/` - 全局样式

### 工具和配置
- `vite.config.ts` - Vite构建配置
- `tsconfig.json` - TypeScript配置
- `package.json` - 项目依赖

## 变更记录 (Changelog)

**2025-11-21**: 初始模块文档生成，基于代码扫描和架构分析