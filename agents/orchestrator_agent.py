"""
Orchestrator Agent (Agent1) - Coordinates all other agents.
"""
from typing import Dict, Any, Optional
import asyncio
from agents.base_agent import BaseAgent
from agents.web_navigator import WebNavigatorAgent
from agents.product_search_agent import ProductSearchAgent
from agents.cart_checkout_agent import CartCheckoutAgent
from config import Config
from utils.action_tracker import ActionTracker
from utils.script_generator import PlaywrightScriptGenerator
import os
from datetime import datetime

class OrchestratorAgent(BaseAgent):
    """Main orchestrator agent that coordinates all other agents."""
    
    def __init__(self, openai_client):
        super().__init__("Orchestrator", openai_client)
        
        # Initialize action tracker
        self.action_tracker = ActionTracker()
        
        # Initialize sub-agents with action tracker
        self.web_navigator = WebNavigatorAgent(openai_client, self.action_tracker)
        self.product_search = ProductSearchAgent(openai_client, self.web_navigator)
        self.cart_checkout = CartCheckoutAgent(openai_client, self.web_navigator)
        
        self.log("Orchestrator agent initialized with all sub-agents")
    
    async def plan_task(self, user_query: str) -> Dict[str, Any]:
        """Create a task plan using OpenAI."""
        try:
            prompt = f"""
            Given a user query for web scraping and e-commerce tasks, create a step-by-step plan.
            The plan should include:
            1. Product search and identification
            2. Navigation to product page
            3. Adding to cart
            4. Checkout process (if requested)
            
            User Query: {user_query}
            
            Return a JSON object with:
            - steps: Array of step objects, each with:
              - step_number: Integer
              - agent: "ProductSearch", "WebNavigator", or "CartCheckout"
              - action: Description of the action
              - expected_result: What should happen
            
            Return only valid JSON.
            """
            
            response = await self.openai_client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a task planning assistant. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                timeout=30.0
            )
            
            import json
            plan = json.loads(response.choices[0].message.content)
            self.log(f"Task plan created: {plan}")
            return plan
        
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                self.log("API quota exceeded, using default plan", "warning")
            else:
                self.log(f"Error creating task plan: {error_msg}, using default plan", "warning")
            # Return default plan
            return {
                "steps": [
                    {"step_number": 1, "agent": "ProductSearch", "action": "search_product", "expected_result": "Find product"},
                    {"step_number": 2, "agent": "CartCheckout", "action": "add_to_cart", "expected_result": "Add product to cart"},
                    {"step_number": 3, "agent": "CartCheckout", "action": "full_checkout", "expected_result": "Complete checkout"}
                ]
            }
    
    async def execute_plan(self, plan: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """Execute the planned task step by step."""
        results = []
        context = {}
        
        try:
            steps = plan.get("steps", [])
            
            for step in steps:
                step_num = step.get("step_number", 0)
                agent_name = step.get("agent", "")
                action = step.get("action", "")
                
                self.log(f"Executing step {step_num}: {agent_name} - {action}")
                
                # Route to appropriate agent
                if agent_name == "ProductSearch":
                    result = await self.product_search.execute({
                        "query": user_query,
                        "action": action
                    }, context)
                    context["product_search_result"] = result
                    
                    # If product found, navigate to product page
                    if result.get("status") == "success" and result.get("data", {}).get("products"):
                        products = result["data"]["products"]
                        if products and len(products) > 0:
                            # Use first matching product
                            product = products[0]
                            if product.get("link"):
                                nav_result = await self.web_navigator.execute({
                                    "action": "navigate",
                                    "url": product["link"]
                                })
                                context["product_page"] = nav_result
                
                elif agent_name == "WebNavigator":
                    result = await self.web_navigator.execute({
                        "action": action,
                        **step  # Include other step parameters
                    }, context)
                    context["navigation_result"] = result
                
                elif agent_name == "CartCheckout":
                    if action == "full_checkout":
                        result = await self.cart_checkout.execute({
                            "action": "full_checkout"
                        }, context)
                    else:
                        result = await self.cart_checkout.execute({
                            "action": action,
                            **step
                        }, context)
                    context["checkout_result"] = result
                
                else:
                    result = {
                        "status": "error",
                        "data": {},
                        "message": f"Unknown agent: {agent_name}"
                    }
                
                results.append({
                    "step": step_num,
                    "agent": agent_name,
                    "action": action,
                    "result": result
                })
                
                # Stop if critical step fails
                if result.get("status") == "error" and step_num <= 2:
                    self.log(f"Critical step {step_num} failed, stopping execution", "warning")
                    break
            
            return {
                "status": "success",
                "data": {
                    "steps_completed": len(results),
                    "results": results,
                    "context": context
                },
                "message": f"Completed {len(results)} steps"
            }
        
        except Exception as e:
            self.log(f"Error executing plan: {str(e)}", "error")
            return {
                "status": "error",
                "data": {"results": results},
                "message": str(e)
            }
    
    async def execute(self, task: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the main orchestration task."""
        try:
            user_query = task.get("query", "")
            
            if not user_query:
                return {
                    "status": "error",
                    "data": {},
                    "message": "No query provided"
                }
            
            self.log(f"Starting orchestration for query: {user_query}")
            
            # Start action tracking
            self.action_tracker.start()
            
            # Step 1: Initialize browser (with retry)
            max_retries = 3
            browser_initialized = False
            for attempt in range(max_retries):
                try:
                    success = await self.web_navigator.initialize_browser(headless=Config.BROWSER_HEADLESS)
                    if success:
                        browser_initialized = True
                        break
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
                        self.log(f"Retrying browser initialization (attempt {attempt + 2}/{max_retries})")
                except Exception as e:
                    self.log(f"Browser initialization attempt {attempt + 1} failed: {str(e)}", "warning")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)
            
            if not browser_initialized:
                return {
                    "status": "error",
                    "data": {},
                    "message": "Failed to initialize browser after multiple attempts. Please ensure Playwright is properly installed."
                }
            
            # Step 2: Plan the task
            self.log("Creating task plan...")
            plan = await self.plan_task(user_query)
            
            # Step 3: Execute the plan
            self.log("Executing task plan...")
            result = await self.execute_plan(plan, user_query)
            
            # Step 4: Take final screenshot and get video
            await self.web_navigator.take_screenshot("final_state.png")
            
            # Get video path if available
            video_path = await self.web_navigator.get_video_path()
            if video_path:
                self.log(f"Video recording saved to: {video_path}")
            
            # Step 5: Stop tracking and generate test script
            self.action_tracker.stop()
            self.log("Generating Playwright test script from execution...")
            script_generator = PlaywrightScriptGenerator(self.action_tracker.get_actions(), user_query)
            
            # Generate script filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_filename = f"test_generated_{timestamp}.py"
            script_path = script_generator.save(script_filename)
            self.log(f"Test script generated and saved to: {script_path}")
            
            return {
                "status": result["status"],
                "data": {
                    "query": user_query,
                    "plan": plan,
                    "execution": result,
                    "test_script": script_path
                },
                "message": f"Orchestration completed with status: {result['status']}. Test script saved to {script_path}"
            }
        
        except Exception as e:
            self.log(f"Error in orchestration: {str(e)}", "error")
            return {
                "status": "error",
                "data": {},
                "message": str(e)
            }
        finally:
            # Cleanup
            await self.web_navigator.close()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.web_navigator.close()

