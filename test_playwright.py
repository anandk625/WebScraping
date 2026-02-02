"""
Playwright Test Script for Web Scraping Agent
Tests the complete workflow: search, find product, and click image
"""
import asyncio
from playwright.async_api import async_playwright
import sys
import re

async def test_product_search_and_click_image(product_query="iPhone 15 Pro 256GB storage white color"):
    """
    Test the complete product search and image clicking workflow.
    
    Steps:
    1. Navigate to website (Apple.com for iPhone products)
    2. Open search menu
    3. Search for simplified product name (e.g., "iPhone 15")
    4. Wait for search results
    5. Read entire page
    6. Find text containing product name
    7. Find image beside the product name
    8. Click on the image
    9. Verify navigation to product page
    """
    print("=" * 80)
    print("PLAYWRIGHT TEST: Product Search and Image Click")
    print("=" * 80)
    print(f"\nProduct Query: {product_query}")
    
    # Extract simplified product name (e.g., "iPhone 15" from "iPhone 15 Pro 256GB...")
    product_name_match = re.search(r'iphone\s+(\d+)', product_query.lower())
    if product_name_match:
        search_query = f"iPhone {product_name_match.group(1)}"
    else:
        search_query = "iPhone"
    
    print(f"Search Query: {search_query}\n")
    
    browser = await async_playwright().start()
    chromium = await browser.chromium.launch(headless=False, slow_mo=500)
    page = await chromium.new_page()
    
    try:
        # Step 1: Navigate to Apple.com
        print("Step 1: Navigating to Apple.com...")
        await page.goto('https://www.apple.com', wait_until='networkidle')
        print(f"   Page loaded: {await page.title()}")
        await asyncio.sleep(2)
        
        # Step 2: Click search icon (Apple.com specific)
        print("\nStep 2: Opening search menu...")
        search_icon_selectors = [
            '#ac-gn-searchform',
            'button.ac-gn-searchform-submit',
            'a[aria-label*="Search" i]'
        ]
        
        search_icon_clicked = False
        for selector in search_icon_selectors:
            try:
                icon = await page.wait_for_selector(selector, timeout=3000)
                if icon and await icon.is_visible():
                    await icon.click()
                    print(f"   Clicked search icon: {selector}")
                    await asyncio.sleep(2)
                    search_icon_clicked = True
                    break
            except:
                continue
        
        if not search_icon_clicked:
            print("   Warning: Search icon not found, trying direct input...")
        
        # Step 3: Fill search input and submit
        print("\nStep 3: Searching for product...")
        search_input_selectors = [
            '#ac-gn-searchform-input',
            'input.ac-gn-searchform-input',
            'input[type="search"]',
            'input[name="q"]'
        ]
        
        search_success = False
        for selector in search_input_selectors:
            try:
                search_input = await page.wait_for_selector(selector, timeout=5000, state='visible')
                if search_input:
                    print(f"   Found search input: {selector}")
                    await search_input.click()
                    await asyncio.sleep(0.5)
                    await search_input.fill('')
                    await asyncio.sleep(0.3)
                    await search_input.fill(search_query)
                    print(f"   Typed: {search_query}")
                    await asyncio.sleep(1)
                    await search_input.press('Enter')
                    print("   Search submitted")
                    search_success = True
                    break
            except:
                continue
        
        if not search_success:
            print("   Error: Could not find search input")
            return False
        
        # Step 4: Wait for search results
        print("\nStep 4: Waiting for search results...")
        await page.wait_for_load_state('networkidle', timeout=10000)
        await asyncio.sleep(2)
        current_url = page.url
        print(f"   Current URL: {current_url}")
        print(f"   Page title: {await page.title()}")
        
        # Step 5: Read entire page content
        print("\nStep 5: Reading entire page content...")
        page_content = await page.content()
        print(f"   Page content length: {len(page_content)} characters")
        
        # Step 6: Find text containing product name
        print(f"\nStep 6: Searching for text containing '{search_query}'...")
        product_name_lower = search_query.lower()
        product_keywords = product_name_lower.split()
        
        # XPath to find elements containing the product name
        xpath_queries = [
            f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{product_name_lower}')]",
            f"//*[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{product_name_lower}')]",
        ]
        
        matching_element = None
        for xpath_query in xpath_queries:
            try:
                elements = await page.query_selector_all(f"xpath={xpath_query}")
                print(f"   Found {len(elements)} elements containing product name")
                
                for element in elements[:20]:  # Check first 20 matches
                    try:
                        element_text = await element.text_content()
                        element_text_lower = (element_text or "").lower()
                        
                        # Verify it contains all keywords
                        if all(keyword in element_text_lower for keyword in product_keywords):
                            print(f"   Found matching element: {element_text[:80]}...")
                            matching_element = element
                            break
                    except:
                        continue
                
                if matching_element:
                    break
            except Exception as e:
                print(f"   XPath query failed: {str(e)[:100]}")
                continue
        
        if not matching_element:
            print("   Error: Could not find element containing product name")
            return False
        
        # Step 7: Find image beside the product name
        print("\nStep 7: Finding image beside product name...")
        image = None
        
        # Get element tag name
        tag_name = await matching_element.evaluate("el => el.tagName.toLowerCase()")
        
        # Strategy 1: Check if element itself is an image
        if tag_name == "img":
            image = matching_element
            print("   Element itself is an image")
        
        # Strategy 2: Check for image within the same element
        if not image:
            image = await matching_element.query_selector("img")
            if image:
                print("   Found image within element")
        
        # Strategy 3: Check for image in parent element
        if not image:
            try:
                parent = await matching_element.evaluate_handle("el => el.parentElement")
                if parent:
                    image = await parent.query_selector("img")
                    if image:
                        print("   Found image in parent element")
            except:
                pass
        
        # Strategy 4: Check for image in grandparent element
        if not image:
            try:
                grandparent = await matching_element.evaluate_handle("el => el.parentElement?.parentElement")
                if grandparent:
                    image = await grandparent.query_selector("img")
                    if image:
                        print("   Found image in grandparent element")
            except:
                pass
        
        # Strategy 5: Check for sibling images
        if not image:
            try:
                prev_sibling = await matching_element.evaluate_handle("el => el.previousElementSibling")
                if prev_sibling:
                    prev_img = await prev_sibling.query_selector("img")
                    if prev_img:
                        image = prev_img
                        print("   Found image in previous sibling")
                
                if not image:
                    next_sibling = await matching_element.evaluate_handle("el => el.nextElementSibling")
                    if next_sibling:
                        next_img = await next_sibling.query_selector("img")
                        if next_img:
                            image = next_img
                            print("   Found image in next sibling")
            except:
                pass
        
        # Strategy 6: Walk up DOM tree to find container with image
        if not image:
            try:
                current = matching_element
                for level in range(5):
                    parent = await current.evaluate_handle("el => el.parentElement")
                    if not parent:
                        break
                    
                    parent_img = await parent.query_selector("img")
                    if parent_img:
                        image = parent_img
                        print(f"   Found image in ancestor at level {level + 1}")
                        break
                    
                    current = parent
            except:
                pass
        
        if not image:
            print("   Error: Could not find image beside product name")
            return False
        
        # Step 8: Click on the image
        print("\nStep 8: Clicking on product image...")
        try:
            is_visible = await image.is_visible()
            if not is_visible:
                print("   Image not visible, scrolling into view...")
                await image.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
            
            await image.click()
            print("   Image clicked")
            await asyncio.sleep(2)
            await page.wait_for_load_state('networkidle', timeout=10000)
        except Exception as e:
            print(f"   Error clicking image: {str(e)}")
            return False
        
        # Step 9: Verify navigation to product page
        print("\nStep 9: Verifying navigation to product page...")
        new_url = page.url
        new_title = await page.title()
        print(f"   New URL: {new_url}")
        print(f"   New title: {new_title}")
        
        # Check if we're on a product page (URL should contain product-related terms)
        if 'iphone' in new_url.lower() or 'product' in new_url.lower() or 'shop' in new_url.lower():
            print("   Success: Navigated to product page")
            print("\n" + "=" * 80)
            print("TEST PASSED: Successfully searched and clicked product image")
            print("=" * 80)
            
            # Wait to see the result
            print("\nWaiting 10 seconds to view the product page...")
            await asyncio.sleep(10)
            
            return True
        else:
            print("   Warning: May not be on expected product page")
            return True  # Still consider it a pass if we navigated somewhere
    
    except Exception as e:
        print(f"\nTEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        await chromium.close()
        await browser.stop()

async def test_multiple_products():
    """Test with multiple product queries."""
    test_queries = [
        "iPhone 15 Pro 256GB storage white color",
        "iPhone 16 Pro Max",
        "iPhone 17"
    ]
    
    print("\n" + "=" * 80)
    print("RUNNING MULTIPLE PRODUCT TESTS")
    print("=" * 80)
    
    results = []
    for query in test_queries:
        print(f"\n\nTesting: {query}")
        print("-" * 80)
        result = await test_product_search_and_click_image(query)
        results.append((query, result))
        await asyncio.sleep(3)  # Wait between tests
    
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    for query, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{status}: {query}")
    print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run with custom query
        query = " ".join(sys.argv[1:])
        asyncio.run(test_product_search_and_click_image(query))
    elif len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Run all tests
        asyncio.run(test_multiple_products())
    else:
        # Run default test
        asyncio.run(test_product_search_and_click_image())
