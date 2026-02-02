"""
Main entry point for the Web Scraping Agent system.
"""
import asyncio
import sys
from openai import AsyncOpenAI
from config import Config
from utils.logger import setup_logger
from agents.orchestrator_agent import OrchestratorAgent

logger = setup_logger()

async def main():
    """Main function to run the web scraping agent."""
    try:
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
            # Example query
            user_query = input("Enter your product search query (e.g., 'iPhone 15 Pro 256GB storage white color'): ").strip()
            if not user_query:
                user_query = "iPhone 15 Pro 256GB storage white color"
                logger.info(f"No query provided, using example: {user_query}")
        
        logger.info(f"Starting web scraping agent with query: {user_query}")
        
        # Initialize orchestrator agent
        orchestrator = OrchestratorAgent(client)
        
        # Execute task
        result = await orchestrator.execute({
            "query": user_query
        })
        
        # Print results
        print("\n" + "="*80)
        print("EXECUTION RESULTS")
        print("="*80)
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print("\nExecution Details:")
        
        if result.get("data", {}).get("execution"):
            execution = result["data"]["execution"]
            if execution.get("data", {}).get("results"):
                for step_result in execution["data"]["results"]:
                    print(f"\nStep {step_result['step']}: {step_result['agent']} - {step_result['action']}")
                    print(f"  Status: {step_result['result']['status']}")
                    print(f"  Message: {step_result['result']['message']}")
        
        print("\n" + "="*80)
        print("\n⚠️  Browser will stay open for 10 seconds so you can see the final state...")
        print("   Close the browser window manually or wait for it to close automatically.\n")
        
        # Keep browser open for a bit so user can see
        await asyncio.sleep(10)
        
        # Cleanup
        await orchestrator.cleanup()
        
        return result
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return None
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        print(f"\nError: {str(e)}")
        return None

if __name__ == "__main__":
    asyncio.run(main())

