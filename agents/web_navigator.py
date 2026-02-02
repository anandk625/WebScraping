"""
Web Navigator Agent - Handles browser automation and navigation.
"""
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from agents.base_agent import BaseAgent
import asyncio

class WebNavigatorAgent(BaseAgent):
    """Agent responsible for web navigation and browser automation."""
    
    def __init__(self, openai_client, action_tracker=None):
        super().__init__("WebNavigator", openai_client)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.action_tracker = action_tracker
    
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.page:
                try:
                    await self.page.close()
                except:
                    pass
                self.page = None
        except:
            pass
        
        try:
            if self.context:
                try:
                    await self.context.close()
                except:
                    pass
                self.context = None
        except:
            pass
        
        try:
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
                self.browser = None
        except:
            pass
        
        try:
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
                self.playwright = None
        except:
            pass
    
    async def initialize_browser(self, headless: bool = False):
        """Initialize the browser instance."""
        try:
            # Clean up any existing instances first
            await self._cleanup_browser()
            await asyncio.sleep(1)  # Longer wait for cleanup
            
            self.log("Starting Playwright...")
            # Initialize fresh browser instance
            self.playwright = await async_playwright().start()
            await asyncio.sleep(1)
            
            self.log(f"Launching browser (headless={headless})...")
            # Launch browser - try multiple approaches
            browser_launched = False
            
            if not headless:
                # Try using system Chrome first (more stable on macOS)
                try:
                    self.log("Trying to use system Chrome...")
                    self.browser = await self.playwright.chromium.launch(
                        headless=False,
                        channel='chrome',  # Use system Chrome if available
                        slow_mo=500
                    )
                    browser_launched = True
                    self.log("✅ Successfully launched system Chrome")
                except Exception as e:
                    self.log(f"System Chrome not available: {e}, trying bundled Chromium", "warning")
            
            if not browser_launched:
                # Use bundled Chromium
                try:
                    if headless:
                        self.browser = await self.playwright.chromium.launch(
                            headless=True,
                            args=['--no-sandbox', '--disable-dev-shm-usage']
                        )
                    else:
                        # For visible mode - minimal args for stability
                        self.browser = await self.playwright.chromium.launch(
                            headless=False,
                            slow_mo=500,
                            args=[]  # No special args - let it use defaults
                        )
                    browser_launched = True
                    self.log("✅ Successfully launched bundled Chromium")
                except Exception as launch_error:
                    self.log(f"Bundled Chromium launch failed: {launch_error}", "error")
                    raise
            
            await asyncio.sleep(2)  # Give browser plenty of time to start
            
            self.log("Creating browser context...")
            # Simple context
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            await asyncio.sleep(1)
            
            self.log("Creating new page...")
            self.page = await self.context.new_page()
            await asyncio.sleep(1)
            
            # Verify it's working
            try:
                current_url = self.page.url
                self.log(f"Page created successfully. Current URL: {current_url}")
            except Exception as e:
                self.log(f"Warning: Could not get page URL: {str(e)}", "warning")
            
            self.log("✅ Browser initialized successfully and ready!")
            return True
        except Exception as e:
            self.log(f"Failed to initialize browser: {str(e)}", "error")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}", "error")
            await self._cleanup_browser()
            return False
    
    async def navigate_to(self, url: str) -> bool:
        """Navigate to a specific URL."""
        try:
            if not self.page:
                await self.initialize_browser()
            
            # Check if page is still valid
            try:
                _ = self.page.url
            except:
                self.log("Page was closed, reinitializing browser...", "warning")
                await self.initialize_browser()
            
            self.log(f"🌐 Navigating to: {url}")
            if self.action_tracker:
                self.action_tracker.add_navigation(url)
            await self.page.goto(url, wait_until="networkidle", timeout=60000)
            await asyncio.sleep(4)  # Wait longer so user can see the page load
            if self.action_tracker:
                self.action_tracker.add_wait("load", timeout=60000)
                self.action_tracker.add_sleep(4)
            
            # Verify page is still open
            try:
                current_url = self.page.url
                self.log(f"✅ Successfully navigated to: {url} (current: {current_url})")
            except:
                self.log("⚠️  Page closed after navigation", "warning")
                return False
            return True
        except Exception as e:
            self.log(f"Failed to navigate to {url}: {str(e)}", "error")
            # Try to reinitialize if page was closed
            if "closed" in str(e).lower():
                self.log("Attempting to reinitialize browser...", "warning")
                await self.initialize_browser()
            return False
    
    async def find_element(self, selector: str, timeout: int = 10000) -> Optional[Any]:
        """Find an element on the page."""
        try:
            element = await self.page.wait_for_selector(selector, timeout=timeout)
            return element
        except Exception as e:
            self.log(f"Element not found with selector {selector}: {str(e)}", "warning")
            return None
    
    async def click(self, selector: str) -> bool:
        """Click on an element."""
        try:
            element = await self.find_element(selector)
            if element:
                self.log(f"🖱️  Clicking on: {selector}")
                if self.action_tracker:
                    self.action_tracker.add_click(selector, element_type="element")
                await element.click()
                await asyncio.sleep(3)  # Longer delay so user can see the action
                if self.action_tracker:
                    self.action_tracker.add_sleep(3)
                self.log(f"✅ Successfully clicked!")
                return True
            return False
        except Exception as e:
            self.log(f"Failed to click on {selector}: {str(e)}", "error")
            return False
    
    async def fill_input(self, selector: str, text: str) -> bool:
        """Fill an input field."""
        try:
            element = await self.find_element(selector)
            if element:
                self.log(f"⌨️  Typing in {selector}: {text}")
                if self.action_tracker:
                    self.action_tracker.add_fill(selector, text)
                await element.fill(text)
                await asyncio.sleep(2)  # Longer delay so user can see typing
                if self.action_tracker:
                    self.action_tracker.add_sleep(2)
                self.log(f"✅ Successfully filled input!")
                return True
            return False
        except Exception as e:
            self.log(f"Failed to fill input {selector}: {str(e)}", "error")
            return False
    
    async def get_page_content(self) -> str:
        """Get the current page content."""
        try:
            content = await self.page.content()
            return content
        except Exception as e:
            self.log(f"Failed to get page content: {str(e)}", "error")
            return ""
    
    async def get_page_url(self) -> str:
        """Get the current page URL."""
        try:
            return self.page.url
        except Exception as e:
            self.log(f"Failed to get page URL: {str(e)}", "error")
            return ""
    
    async def take_screenshot(self, path: str = "screenshot.png") -> bool:
        """Take a screenshot of the current page."""
        try:
            await self.page.screenshot(path=path, full_page=True)
            self.log(f"Screenshot saved to: {path}")
            return True
        except Exception as e:
            self.log(f"Failed to take screenshot: {str(e)}", "error")
            return False
    
    async def get_video_path(self) -> Optional[str]:
        """Get the path to the recorded video."""
        try:
            if self.page:
                video = await self.page.video
                if video:
                    return await video.path()
        except:
            pass
        return None
    
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute navigation tasks."""
        try:
            action = task.get("action")
            
            if action == "navigate":
                url = task.get("url")
                success = await self.navigate_to(url)
                return {
                    "status": "success" if success else "error",
                    "data": {"url": url, "current_url": await self.get_page_url()},
                    "message": f"Navigation {'successful' if success else 'failed'}"
                }
            
            elif action == "click":
                selector = task.get("selector")
                success = await self.click(selector)
                return {
                    "status": "success" if success else "error",
                    "data": {"selector": selector},
                    "message": f"Click {'successful' if success else 'failed'}"
                }
            
            elif action == "fill":
                selector = task.get("selector")
                text = task.get("text")
                success = await self.fill_input(selector, text)
                return {
                    "status": "success" if success else "error",
                    "data": {"selector": selector, "text": text},
                    "message": f"Fill {'successful' if success else 'failed'}"
                }
            
            elif action == "get_content":
                content = await self.get_page_content()
                return {
                    "status": "success",
                    "data": {"content": content, "url": await self.get_page_url()},
                    "message": "Content retrieved successfully"
                }
            
            else:
                return {
                    "status": "error",
                    "data": {},
                    "message": f"Unknown action: {action}"
                }
        
        except Exception as e:
            self.log(f"Error executing task: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def close(self):
        """Close the browser and cleanup."""
        await self._cleanup_browser()
        self.log("Browser closed successfully")

