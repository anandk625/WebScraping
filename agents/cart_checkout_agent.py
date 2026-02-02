"""
Cart and Checkout Agent - Handles adding to cart and checkout process.
"""
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.web_navigator import WebNavigatorAgent
from config import Config
import asyncio

class CartCheckoutAgent(BaseAgent):
    """Agent responsible for cart operations and checkout process."""
    
    def __init__(self, openai_client, web_navigator: WebNavigatorAgent):
        super().__init__("CartCheckout", openai_client)
        self.web_navigator = web_navigator
    
    async def find_add_to_cart_strategy(self, current_url: str) -> Dict[str, Any]:
        """Determine how to add product to cart using OpenAI."""
        try:
            page_content = await self.web_navigator.get_page_content()
            content_preview = page_content[:5000] if len(page_content) > 5000 else page_content
            
            prompt = f"""
            Analyze the HTML content and determine how to add a product to cart.
            Return a JSON object with:
            - add_to_cart_selector: CSS selector for the "Add to Cart" button
            - cart_button_selector: CSS selector for the cart icon/button (if needed to view cart)
            - checkout_button_selector: CSS selector for the checkout button (if visible)
            
            Current URL: {current_url}
            HTML Content (preview): {content_preview}
            
            Return only valid JSON. If elements are not found, use common selectors like:
            - button:contains("Add to Cart"), button:contains("Add to Bag"), [data-testid*="add-to-cart"]
            - a:contains("Cart"), [aria-label*="cart"]
            - button:contains("Checkout"), button:contains("Buy Now")
            """
            
            response = await self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing e-commerce pages. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            strategy = json.loads(response.choices[0].message.content)
            self.log(f"Add to cart strategy determined: {strategy}")
            return strategy
        
        except Exception as e:
            self.log(f"Error finding add to cart strategy: {str(e)}", "error")
            # Fallback selectors
            return {
                "add_to_cart_selector": "button:has-text('Add to Cart'), button:has-text('Add to Bag'), [data-testid*='add-to-cart']",
                "cart_button_selector": "a:has-text('Cart'), [aria-label*='cart']",
                "checkout_button_selector": "button:has-text('Checkout'), button:has-text('Buy Now')"
            }
    
    async def add_to_cart(self, product_selector: Optional[str] = None) -> Dict[str, Any]:
        """Add product to cart."""
        try:
            current_url = await self.web_navigator.get_page_url()
            
            # Find add to cart strategy
            strategy = await self.find_add_to_cart_strategy(current_url)
            
            # Try to click add to cart button
            add_to_cart_selector = strategy.get("add_to_cart_selector", "")
            
            # Try multiple common selectors
            selectors_to_try = [
                add_to_cart_selector,
                "button:has-text('Add to Cart')",
                "button:has-text('Add to Bag')",
                "[data-testid*='add-to-cart']",
                "button[aria-label*='Add to Cart']",
                ".add-to-cart",
                "#add-to-cart"
            ]
            
            clicked = False
            for selector in selectors_to_try:
                if selector and await self.web_navigator.click(selector):
                    clicked = True
                    await asyncio.sleep(2)  # Wait for cart to update
                    break
            
            if not clicked:
                return {
                    "status": "error",
                    "data": {},
                    "message": "Could not find or click 'Add to Cart' button"
                }
            
            self.log("Product added to cart successfully")
            return {
                "status": "success",
                "data": {"action": "add_to_cart"},
                "message": "Product added to cart"
            }
        
        except Exception as e:
            self.log(f"Error adding to cart: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def navigate_to_cart(self) -> Dict[str, Any]:
        """Navigate to the cart page."""
        try:
            # Try to find and click cart button
            cart_selectors = [
                "a:has-text('Cart')",
                "[aria-label*='cart']",
                ".cart-icon",
                "#cart",
                "a[href*='cart']"
            ]
            
            for selector in cart_selectors:
                if await self.web_navigator.click(selector):
                    await asyncio.sleep(2)
                    self.log("Navigated to cart")
                    return {
                        "status": "success",
                        "data": {"action": "navigate_to_cart"},
                        "message": "Navigated to cart"
                    }
            
            return {
                "status": "error",
                "data": {},
                "message": "Could not navigate to cart"
            }
        
        except Exception as e:
            self.log(f"Error navigating to cart: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def proceed_to_checkout(self) -> Dict[str, Any]:
        """Proceed to checkout."""
        try:
            # Try to find checkout button
            checkout_selectors = [
                "button:has-text('Checkout')",
                "button:has-text('Proceed to Checkout')",
                "a:has-text('Checkout')",
                "[data-testid*='checkout']",
                "button[aria-label*='checkout']"
            ]
            
            for selector in checkout_selectors:
                if await self.web_navigator.click(selector):
                    await asyncio.sleep(3)  # Wait for checkout page to load
                    self.log("Proceeded to checkout")
                    return {
                        "status": "success",
                        "data": {"action": "proceed_to_checkout"},
                        "message": "Proceeded to checkout"
                    }
            
            return {
                "status": "error",
                "data": {},
                "message": "Could not find checkout button"
            }
        
        except Exception as e:
            self.log(f"Error proceeding to checkout: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def fill_checkout_form(self, user_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fill checkout form with user information."""
        try:
            if not user_info:
                # Use default test data (in production, this would come from user)
                user_info = {
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                    "address": "123 Test St",
                    "city": "Test City",
                    "zip": "12345",
                    "phone": "1234567890"
                }
            
            # Use OpenAI to determine form field selectors
            page_content = await self.web_navigator.get_page_content()
            content_preview = page_content[:3000] if len(page_content) > 3000 else page_content
            
            prompt = f"""
            Analyze the HTML content and determine CSS selectors for checkout form fields.
            Return a JSON object with selectors for:
            - email: Email input field
            - first_name: First name input field
            - last_name: Last name input field
            - address: Address input field
            - city: City input field
            - zip: ZIP/Postal code input field
            - phone: Phone input field
            - continue_button: Continue/Next button
            
            HTML Content (preview): {content_preview}
            
            Return only valid JSON.
            """
            
            response = await self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing forms. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            import json
            form_selectors = json.loads(response.choices[0].message.content)
            
            # Fill form fields
            filled_fields = []
            for field, selector in form_selectors.items():
                if field in user_info and selector:
                    value = user_info[field]
                    if await self.web_navigator.fill_input(selector, value):
                        filled_fields.append(field)
                        await asyncio.sleep(0.5)
            
            self.log(f"Filled {len(filled_fields)} form fields")
            
            # Click continue button if available
            if form_selectors.get("continue_button"):
                await self.web_navigator.click(form_selectors["continue_button"])
                await asyncio.sleep(2)
            
            return {
                "status": "success",
                "data": {"filled_fields": filled_fields},
                "message": f"Filled {len(filled_fields)} form fields"
            }
        
        except Exception as e:
            self.log(f"Error filling checkout form: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def place_order(self) -> Dict[str, Any]:
        """Place the final order."""
        try:
            # Look for place order button
            order_selectors = [
                "button:has-text('Place Order')",
                "button:has-text('Complete Order')",
                "button:has-text('Buy Now')",
                "[data-testid*='place-order']",
                "button[type='submit']:has-text('Order')"
            ]
            
            for selector in order_selectors:
                if await self.web_navigator.click(selector):
                    await asyncio.sleep(3)
                    self.log("Order placed successfully")
                    return {
                        "status": "success",
                        "data": {"action": "place_order"},
                        "message": "Order placed successfully"
                    }
            
            return {
                "status": "error",
                "data": {},
                "message": "Could not find place order button. Note: Actual payment processing may require additional steps."
            }
        
        except Exception as e:
            self.log(f"Error placing order: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
    
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute cart/checkout task."""
        try:
            action = task.get("action")
            
            if action == "add_to_cart":
                return await self.add_to_cart(task.get("product_selector"))
            
            elif action == "navigate_to_cart":
                return await self.navigate_to_cart()
            
            elif action == "proceed_to_checkout":
                return await self.proceed_to_checkout()
            
            elif action == "fill_checkout_form":
                return await self.fill_checkout_form(task.get("user_info"))
            
            elif action == "place_order":
                return await self.place_order()
            
            elif action == "full_checkout":
                # Complete checkout flow
                results = []
                
                # Add to cart
                result = await self.add_to_cart()
                results.append(result)
                if result["status"] != "success":
                    return {"status": "error", "data": {"steps": results}, "message": "Failed at add to cart step"}
                
                # Navigate to cart
                result = await self.navigate_to_cart()
                results.append(result)
                
                # Proceed to checkout
                result = await self.proceed_to_checkout()
                results.append(result)
                if result["status"] != "success":
                    return {"status": "partial", "data": {"steps": results}, "message": "Reached checkout but may need manual completion"}
                
                # Fill form (optional, may not be needed for all sites)
                # result = await self.fill_checkout_form()
                # results.append(result)
                
                # Place order (this would typically require payment info)
                # result = await self.place_order()
                # results.append(result)
                
                return {
                    "status": "success",
                    "data": {"steps": results},
                    "message": "Checkout process initiated. Note: Final order placement may require payment information."
                }
            
            else:
                return {
                    "status": "error",
                    "data": {},
                    "message": f"Unknown action: {action}"
                }
        
        except Exception as e:
            self.log(f"Error executing cart/checkout task: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }

