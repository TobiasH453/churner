from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
from models import EmailData, AgentResponse
from browser_agent import BrowserAgent
from utils import logger, get_env

app = FastAPI(title="Amazon Order Automation Agent")
agent = BrowserAgent()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Amazon Order Automation Agent"}

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "browser_headless": get_env("BROWSER_HEADLESS", "false"),
        "max_retries": get_env("MAX_RETRIES", "3")
    }

@app.post("/process-order")
async def process_order(email_data: EmailData) -> AgentResponse:
    """
    Main webhook endpoint called by n8n

    Receives email data, performs browser automation, returns results
    """
    try:
        logger.info(f"Received request for order: {email_data.order_number}")

        # Process the email asynchronously
        result = await agent.process_email(email_data)

        logger.info(f"Completed processing in {result.execution_time_seconds}s")
        return result

    except Exception as e:
        logger.error(f"Error in /process-order endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify server is working"""
    return {
        "message": "Server is working!",
        "test_data": {
            "order_number": "111-2222222-3333333",
            "status": "ready"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(get_env("SERVER_PORT", "8080"))

    logger.info(f"Starting Amazon Order Automation Agent on port {port}")
    logger.info("Browser mode: VISIBLE (you can watch the automation)")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )