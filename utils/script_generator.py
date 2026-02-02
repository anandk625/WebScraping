"""
Script Generator - Generates Playwright test scripts from tracked actions.
"""
from typing import List, Dict, Any
from datetime import datetime
import os

class PlaywrightScriptGenerator:
    """Generates Playwright test scripts from tracked actions."""
    
    def __init__(self, actions: List[Dict[str, Any]], query: str = ""):
        self.actions = actions
        self.query = query
    
    def generate(self) -> str:
        """Generate the Playwright test script."""
        lines = []
        
        # Header
        lines.append('"""')
        lines.append(f"Auto-generated Playwright test script")
        lines.append(f"Generated from execution on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if self.query:
            lines.append(f"Original query: {self.query}")
        lines.append('"""')
        lines.append("import asyncio")
        lines.append("from playwright.async_api import async_playwright")
        lines.append("")
        lines.append("")
        lines.append("async def test_auto_generated():")
        lines.append('    """Auto-generated test based on actual execution."""')
        lines.append("    browser = await async_playwright().start()")
        lines.append("    chromium = await browser.chromium.launch(headless=False, slow_mo=500)")
        lines.append("    page = await chromium.new_page()")
        lines.append("")
        lines.append("    try:")
        
        # Generate actions
        indent = "        "
        for i, action in enumerate(self.actions):
            action_type = action.get("type")
            
            if action_type == "navigate":
                url = action.get("url", "")
                lines.append(f"{indent}# Step {i+1}: Navigate to {url}")
                lines.append(f'{indent}await page.goto("{url}", wait_until="networkidle")')
                lines.append(f'{indent}await asyncio.sleep(2)')
                lines.append("")
            
            elif action_type == "click":
                selector = action.get("selector", "")
                element_type = action.get("element_type", "element")
                
                # Special handling for product images - use XPath or more flexible selectors
                if "product_image" in element_type or "image" in element_type.lower():
                    lines.append(f"{indent}# Step {i+1}: Click {element_type}")
                    lines.append(f'{indent}# Find product image (using flexible selector)')
                    lines.append(f'{indent}images = await page.query_selector_all("img")')
                    lines.append(f'{indent}for img in images:')
                    lines.append(f'{indent}    try:')
                    lines.append(f'{indent}        is_visible = await img.is_visible()')
                    lines.append(f'{indent}        if is_visible:')
                    lines.append(f'{indent}            await img.scroll_into_view_if_needed()')
                    lines.append(f'{indent}            await img.click()')
                    lines.append(f'{indent}            break')
                    lines.append(f'{indent}    except:')
                    lines.append(f'{indent}        continue')
                    lines.append(f'{indent}await asyncio.sleep(2)')
                    lines.append(f'{indent}await page.wait_for_load_state("networkidle", timeout=10000)')
                    lines.append("")
                else:
                    lines.append(f"{indent}# Step {i+1}: Click {element_type}")
                    lines.append(f'{indent}element = await page.wait_for_selector("{selector}", timeout=5000)')
                    lines.append(f'{indent}await element.click()')
                    lines.append(f'{indent}await asyncio.sleep(1)')
                    lines.append("")
            
            elif action_type == "fill":
                selector = action.get("selector", "")
                text = action.get("text", "")
                lines.append(f"{indent}# Step {i+1}: Fill input field")
                lines.append(f'{indent}input = await page.wait_for_selector("{selector}", timeout=5000, state="visible")')
                lines.append(f'{indent}await input.click()')
                lines.append(f'{indent}await input.fill("")')
                lines.append(f'{indent}await input.fill("{text}")')
                lines.append(f'{indent}await asyncio.sleep(0.5)')
                lines.append("")
            
            elif action_type == "press":
                selector = action.get("selector", "")
                key = action.get("key", "Enter")
                lines.append(f"{indent}# Step {i+1}: Press key '{key}'")
                lines.append(f'{indent}element = await page.wait_for_selector("{selector}", timeout=5000)')
                lines.append(f'{indent}await element.press("{key}")')
                lines.append(f'{indent}await asyncio.sleep(1)')
                lines.append("")
            
            elif action_type == "wait":
                wait_type = action.get("wait_type", "load")
                timeout = action.get("timeout", 10000)
                selector = action.get("selector")
                
                if wait_type == "load":
                    lines.append(f"{indent}# Step {i+1}: Wait for page load")
                    lines.append(f'{indent}await page.wait_for_load_state("networkidle", timeout={timeout})')
                elif wait_type == "selector" and selector:
                    lines.append(f"{indent}# Step {i+1}: Wait for selector")
                    lines.append(f'{indent}await page.wait_for_selector("{selector}", timeout={timeout})')
                lines.append("")
            
            elif action_type == "sleep":
                seconds = action.get("seconds", 1)
                lines.append(f"{indent}# Step {i+1}: Wait {seconds} seconds")
                lines.append(f'{indent}await asyncio.sleep({seconds})')
                lines.append("")
        
        # Footer
        lines.append(f"{indent}print('Test completed successfully')")
        lines.append(f'{indent}print(f"Final URL: {{page.url}}")')
        lines.append(f'{indent}print(f"Final title: {{await page.title()}}")')
        lines.append(f'{indent}await asyncio.sleep(5)')
        lines.append("")
        lines.append("    except Exception as e:")
        lines.append('        print(f"Test failed: {str(e)}")')
        lines.append("        import traceback")
        lines.append("        traceback.print_exc()")
        lines.append("")
        lines.append("    finally:")
        lines.append("        await chromium.close()")
        lines.append("        await browser.stop()")
        lines.append("")
        lines.append("")
        lines.append('if __name__ == "__main__":')
        lines.append("    asyncio.run(test_auto_generated())")
        
        return "\n".join(lines)
    
    def save(self, filepath: str):
        """Save the generated script to a file."""
        script_content = self.generate()
        with open(filepath, 'w') as f:
            f.write(script_content)
        return filepath
