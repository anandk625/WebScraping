"""
Demo script to show the agent working in a visible browser.
"""
import asyncio
import sys
from openai import AsyncOpenAI
from config import Config
from utils.logger import setup_logger
from agents.orchestrator_agent import OrchestratorAgent

logger = setup_logger()

async def demo():
    """Demo function with clear visual feedback."""
    try:
        print("\n" + "="*80)
        print("🌐 WEB SCRAPING AGENT DEMO")
        print("="*80)
        print("\nYou will see a browser window open and the agent will:")
        print("  1. Navigate to the product website")
        print("  2. Search for the product")
        print("  3. Find matching products")
        print("  4. Attempt to add to cart")
        print("\nWatch the browser window to see all actions in real-time!")
        print("="*80 + "\n")
        
        # Validate configuration
        Config.validate()
        
        # Initialize OpenAI client
        client = AsyncOpenAI(
            api_key=Config.OPENAI_API_KEY,
            timeout=60.0
        )
        
        # Get user query
        if len(sys.argv) > 1:
            user_query = " ".join(sys.argv[1:])
        else:
            user_query = "iPhone 15 Pro 256GB storage white color"
            print(f"Using demo query: {user_query}\n")
        
        print("🚀 Starting agent...\n")
        
        # Initialize orchestrator agent
        orchestrator = OrchestratorAgent(client)
        
        # Execute task
        result = await orchestrator.execute({
            "query": user_query
        })
        
        # Print results
        print("\n" + "="*80)
        print("✅ EXECUTION COMPLETE")
        print("="*80)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print("\n📊 Execution Details:")
        
        if result.get("data", {}).get("execution"):
            execution = result["data"]["execution"]
            if execution.get("data", {}).get("results"):
                for step_result in execution["data"]["results"]:
                    status_icon = "✅" if step_result['result']['status'] == "success" else "❌"
                    print(f"\n{status_icon} Step {step_result['step']}: {step_result['agent']} - {step_result['action']}")
                    print(f"   Status: {step_result['result']['status']}")
                    print(f"   Message: {step_result['result']['message']}")
        
        # Show test script location
        if result.get("data", {}).get("test_script"):
            test_script = result["data"]["test_script"]
            print("\n" + "="*80)
            print("📝 TEST SCRIPT GENERATED")
            print("="*80)
            print(f"Test script saved to: {test_script}")
            print(f"You can run it with: python {test_script}")
            print("="*80)
        
        print("\n" + "="*80)
        print("\n👀 Browser will stay open for 30 seconds so you can inspect everything...")
        print("   Watch the browser window to see all the actions!")
        print("   You can close the browser window manually or wait for it to close.\n")
        
        # Keep browser open longer for demo
        await asyncio.sleep(30)
        
        # Cleanup
        await orchestrator.cleanup()
        
        print("\n✅ Demo complete! Browser closed.\n")
        return result
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return None
    except Exception as e:
        logger.error(f"Error in demo: {str(e)}")
        print(f"\n❌ Error: {str(e)}\n")
        return None

if __name__ == "__main__":
    asyncio.run(demo())

