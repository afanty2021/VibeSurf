"""
Boss 直聘浏览器会话管理模块

该模块负责管理与 Boss 直聘网站的浏览器会话，
包括登录状态维护、会话保持、异常处理等。
"""

import asyncio
import json
import time
import logging
from typing import Optional, Dict, List, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Locator
from browser_use.agent.service import AgentService
from browser_use.browser.browser import BrowserSession
from browser_use.dom.service import DomService

logger = logging.getLogger(__name__)

@dataclass
class SessionState:
    """会话状态"""
    is_logged_in: bool = False
    user_name: str = ""
    user_id: str = ""
    last_active: datetime = None
    session_cookies: List[Dict] = None
    user_agent: str = ""
    page_title: str = ""

    def __post_init__(self):
        if self.last_active is None:
            self.last_active = datetime.now()
        if self.session_cookies is None:
            self.session_cookies = []

class BossZhipinSessionManager:
    """Boss 直聘会话管理器"""

    def __init__(self,
                 headless: bool = False,
                 user_data_dir: Optional[str] = None,
                 session_file: Optional[str] = None):
        """
        初始化会话管理器

        Args:
            headless: 是否无头模式
            user_data_dir: 浏览器用户数据目录
            session_file: 会话保存文件路径
        """
        self.headless = headless
        self.user_data_dir = user_data_dir or str(Path.home() / ".vibesurf" / "browser_data")
        self.session_file = session_file or str(Path.home() / ".vibesurf" / "boss_zhipin_session.json")

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_state = SessionState()

        # Boss 直聘相关 URL
        self.base_url = "https://www.zhipin.com"
        self.login_url = "https://login.zhipin.com/"
        self.web_url = "https://www.zhipin.com/web/"

    async def initialize(self) -> bool:
        """初始化浏览器和会话"""
        try:
            # 启动 Playwright
            self.playwright = await async_playwright().start()

            # 启动 Chromium 浏览器
            launch_args = {
                "headless": self.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=VizDisplayCompositor",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--no-first-run",
                    "--no-zygote",
                    "--single-process",
                    "--disable-gpu"
                ]
            }

            # 如果指定了用户数据目录，添加到启动参数
            if self.user_data_dir:
                launch_args["user_data_dir"] = self.user_data_dir

            self.browser = await self.playwright.chromium.launch(**launch_args)

            # 创建浏览器上下文
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            self.context = await self.browser.new_context(**context_options)

            # 加载保存的会话
            await self._load_session()

            # 创建新页面
            self.page = await self.context.new_page()

            # 设置额外的客户端代码以避免检测
            await self.page.add_init_script("""
                // 移除 webdriver 标记
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // 修改插件数量
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // 修改语言
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
            """)

            logger.info("浏览器初始化成功")
            return True

        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            await self.cleanup()
            return False

    async def _load_session(self):
        """加载保存的会话"""
        try:
            session_file = Path(self.session_file)
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # 恢复会话状态
                self.session_state = SessionState(**session_data.get('state', {}))

                # 添加 cookies
                if session_data.get('cookies'):
                    await self.context.add_cookies(session_data['cookies'])

                logger.info("会话加载成功")
        except Exception as e:
            logger.error(f"加载会话失败: {e}")

    async def _save_session(self):
        """保存当前会话"""
        try:
            if not self.context:
                return

            # 获取 cookies
            cookies = await self.context.cookies()

            # 保存会话数据
            session_data = {
                "state": asdict(self.session_state),
                "cookies": cookies,
                "timestamp": datetime.now().isoformat()
            }

            # 确保目录存在
            Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)

            # 写入文件
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2, default=str)

            logger.info("会话保存成功")
        except Exception as e:
            logger.error(f"保存会话失败: {e}")

    async def navigate_to_boss(self) -> bool:
        """导航到 Boss 直聘"""
        try:
            await self.page.goto(self.web_url, wait_until="domcontentloaded", timeout=30000)
            await self.page.wait_for_timeout(2000)

            # 检查是否需要登录
            login_element = await self.page.query_selector(".geek-nav")
            if login_element:
                # 已登录
                await self._update_login_state()
                logger.info("已登录状态")
                return True
            else:
                # 需要登录
                logger.info("需要登录")
                return await self._handle_login()

        except Exception as e:
            logger.error(f"导航到 Boss 直聘失败: {e}")
            return False

    async def _update_login_state(self):
        """更新登录状态"""
        try:
            # 获取用户信息
            user_info = await self.page.query_selector(".geek-nav .name")
            if user_info:
                self.session_state.is_logged_in = True
                self.session_state.user_name = await user_info.text_content()
                self.session_state.last_active = datetime.now()
                self.session_state.page_title = await self.page.title()
                logger.info(f"用户已登录: {self.session_state.user_name}")
        except Exception as e:
            logger.error(f"更新登录状态失败: {e}")

    async def _handle_login(self) -> bool:
        """处理登录流程"""
        try:
            logger.info("请手动登录 Boss 直聘...")

            # 等待用户手动登录
            # 这里可以扩展支持二维码登录、账号密码登录等

            # 检查登录是否成功，最多等待60秒
            for _ in range(60):
                await self.page.wait_for_timeout(1000)

                # 检查是否登录成功
                user_info = await self.page.query_selector(".geek-nav .name")
                if user_info:
                    await self._update_login_state()
                    await self._save_session()
                    logger.info("登录成功！")
                    return True

            logger.warning("登录超时，请重试")
            return False

        except Exception as e:
            logger.error(f"登录处理失败: {e}")
            return False

    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            # 导航到 Boss 直聘首页
            if self.page.url != self.web_url:
                await self.page.goto(self.web_url, wait_until="domcontentloaded")

            # 检查是否有用户信息
            user_info = await self.page.query_selector(".geek-nav .name")
            if user_info:
                await self._update_login_state()
                return True

            return False
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False

    async def search_candidates(self,
                               position: str,
                               city: str = "101010100",
                               experience: str = "3") -> bool:
        """搜索候选人"""
        try:
            # 导航到搜索页面
            search_url = f"{self.web_url}web/geek/job?query={position}&city={city}&experience={experience}"
            await self.page.goto(search_url, wait_until="domcontentloaded")

            # 等待搜索结果加载
            await self.page.wait_for_selector(".job-list-box", timeout=10000)

            logger.info(f"搜索完成: {position}")
            return True

        except Exception as e:
            logger.error(f"搜索候选人失败: {e}")
            return False

    async def get_candidate_list(self, page_num: int = 1) -> List[Dict]:
        """获取候选人列表"""
        candidates = []
        try:
            # 等待候选人列表加载
            await self.page.wait_for_selector(".geek-list", timeout=10000)

            # 获取所有候选人卡片
            candidate_cards = await self.page.query_selector_all(".geek-list .geek-card")

            for card in candidate_cards:
                try:
                    candidate = await self._extract_candidate_info(card)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.error(f"提取候选人信息失败: {e}")
                    continue

            logger.info(f"获取到 {len(candidates)} 个候选人")
            return candidates

        except Exception as e:
            logger.error(f"获取候选人列表失败: {e}")
            return []

    async def _extract_candidate_info(self, card_element) -> Optional[Dict]:
        """提取候选人信息"""
        try:
            # 提取基本信息
            name_element = await card_element.query_selector(".geek-name")
            name = await name_element.text_content() if name_element else ""

            position_element = await card_element.query_selector(".geek-job")
            position = await position_element.text_content() if position_element else ""

            company_element = await card_element.query_selector(".geek-company")
            company = await company_element.text_content() if company_element else ""

            experience_element = await card_element.query_selector(".geek-exp")
            experience = await experience_element.text_content() if experience_element else ""

            salary_element = await card_element.query_selector(".geek-salary")
            salary = await salary_element.text_content() if salary_element else ""

            # 提取链接
            link_element = await card_element.query_selector("a")
            href = await link_element.get_attribute('href') if link_element else ""

            # 提取最近活跃时间
            active_element = await card_element.query_selector(".geek-active")
            active_time = await active_element.text_content() if active_element else ""

            candidate = {
                "name": name.strip(),
                "position": position.strip(),
                "company": company.strip(),
                "experience": experience.strip(),
                "salary": salary.strip(),
                "active_time": active_time.strip(),
                "href": href.strip(),
                "contacted": False,  # 是否已联系
                "timestamp": datetime.now().isoformat()
            }

            return candidate

        except Exception as e:
            logger.error(f"提取候选人信息出错: {e}")
            return None

    async def send_message(self, candidate_url: str, message: str) -> bool:
        """发送消息给候选人"""
        try:
            # 打开候选人详情页
            await self.page.goto(candidate_url, wait_until="domcontentloaded")

            # 等待页面加载
            await self.page.wait_for_timeout(2000)

            # 点击沟通按钮
            chat_button = await self.page.query_selector(".start-chat-btn")
            if chat_button:
                await chat_button.click()
                await self.page.wait_for_timeout(1000)

                # 输入消息
                textarea = await self.page.query_selector(".chat-input textarea")
                if textarea:
                    await textarea.fill(message)

                    # 发送消息
                    send_button = await self.page.query_selector(".chat-input .send-btn")
                    if send_button:
                        await send_button.click()
                        await self.page.wait_for_timeout(1000)
                        logger.info(f"消息已发送: {candidate_url}")
                        return True

            logger.warning(f"无法发送消息: {candidate_url}")
            return False

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    async def check_new_messages(self) -> List[Dict]:
        """检查新消息"""
        messages = []
        try:
            # 导航到消息页面
            await self.page.goto(f"{self.web_url}web/geek/chat", wait_until="domcontentloaded")

            # 等待消息列表加载
            await self.page.wait_for_selector(".chat-list", timeout=5000)

            # 获取未读消息
            unread_items = await self.page.query_selector_all(".chat-item.unread")

            for item in unread_items:
                try:
                    message_info = await self._extract_message_info(item)
                    if message_info:
                        messages.append(message_info)
                except Exception as e:
                    logger.error(f"提取消息信息失败: {e}")
                    continue

            return messages

        except Exception as e:
            logger.error(f"检查新消息失败: {e}")
            return []

    async def _extract_message_info(self, message_element) -> Optional[Dict]:
        """提取消息信息"""
        try:
            # 获取发送者信息
            sender_element = await message_element.query_selector(".chat-sender")
            sender = await sender_element.text_content() if sender_element else ""

            # 获取消息内容
            content_element = await message_element.query_selector(".chat-content")
            content = await content_element.text_content() if content_element else ""

            # 获取时间
            time_element = await message_element.query_selector(".chat-time")
            time_str = await time_element.text_content() if time_element else ""

            message = {
                "sender": sender.strip(),
                "content": content.strip(),
                "time": time_str.strip(),
                "replied": False,
                "timestamp": datetime.now().isoformat()
            }

            return message

        except Exception as e:
            logger.error(f"提取消息信息出错: {e}")
            return None

    async def reply_message(self, sender_name: str, reply: str) -> bool:
        """回复消息"""
        try:
            # 查找对应的聊天窗口
            chat_items = await self.page.query_selector_all(".chat-item")

            for item in chat_items:
                sender_element = await item.query_selector(".chat-sender")
                if sender_element:
                    sender = await sender_element.text_content()
                    if sender_name in sender:
                        # 点击进入聊天
                        await item.click()
                        await self.page.wait_for_timeout(1000)

                        # 输入回复
                        textarea = await self.page.query_selector(".chat-input textarea")
                        if textarea:
                            await textarea.fill(reply)

                            # 发送
                            send_button = await self.page.query_selector(".chat-input .send-btn")
                            if send_button:
                                await send_button.click()
                                await self.page.wait_for_timeout(1000)
                                logger.info(f"已回复 {sender_name}")
                                return True

            logger.warning(f"未找到与 {sender_name} 的聊天")
            return False

        except Exception as e:
            logger.error(f"回复消息失败: {e}")
            return False

    async def cleanup(self):
        """清理资源"""
        try:
            # 保存会话
            await self._save_session()

            # 关闭页面
            if self.page:
                await self.page.close()

            # 关闭上下文
            if self.context:
                await self.context.close()

            # 关闭浏览器
            if self.browser:
                await self.browser.close()

            # 关闭 Playwright
            if self.playwright:
                await self.playwright.stop()

            logger.info("资源清理完成")

        except Exception as e:
            logger.error(f"清理资源失败: {e}")

# 使用示例
async def main():
    # 创建会话管理器
    session = BossZhipinSessionManager(headless=False)

    try:
        # 初始化
        if await session.initialize():
            # 导航到 Boss 直聘
            if await session.navigate_to_boss():
                # 搜索候选人
                await session.search_candidates("前端开发", "101010100", "3")

                # 获取候选人列表
                candidates = await session.get_candidate_list()
                print(f"找到 {len(candidates)} 个候选人")

                # 检查新消息
                messages = await session.check_new_messages()
                print(f"有 {len(messages)} 条新消息")

    finally:
        # 清理资源
        await session.cleanup()

if __name__ == "__main__":
    asyncio.run(main())