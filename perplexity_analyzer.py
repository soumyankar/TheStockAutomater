# Create an enhanced perplexity_analyzer.py with debugging and verification capabilities
# enhanced_script = '''#!/usr/bin/env python3

"""
Enhanced Perplexity Portfolio Summary Analyzer
=============================================

This script reads a portfolio summary from the exports/ directory and sends it to 
Perplexity's API for analysis and summarization, with enhanced debugging and verification.

Requirements:
- pip install openai requests python-dotenv

Usage:
1. Set your PERPLEXITY_API_KEY environment variable
2. Ensure your portfolio summary is in exports/portfolio_summary.txt
3. Run: python perplexity_analyzer.py
"""

import os
import requests
import json
import logging
import sys
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Set up logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class PerplexityAnalyzer:
    def __init__(self):
        """Initialize the Perplexity analyzer with API credentials and verification"""
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        logger.info(f"🔐 Loaded API Key: {self.api_key[:5] if self.api_key else 'None'}***")

        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not found!")

        # Perform connection verification before proceeding
        self.client = self._initialize_client_with_verification()

    def _initialize_client_with_verification(self):
        """Initialize OpenAI client with proper configuration and verification"""
        try:
            logger.info("🔧 Initializing OpenAI client for Perplexity API...")
            
            # Initialize client with explicit configuration
            client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.perplexity.ai"
            )
            
            logger.info("✅ OpenAI client initialized successfully")
            
            # Verify the client configuration
            if self._verify_client_connection(client):
                logger.info("✅ Client connection verified successfully")
                return client
            else:
                raise RuntimeError("Client connection verification failed")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize OpenAI client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Provide specific guidance for common errors
            if "proxies" in str(e):
                logger.error("🔍 DIAGNOSIS: This is a version compatibility issue!")
                logger.error("   - Your OpenAI library version is incompatible with current httpx version")
                logger.error("   - Solution 1: Update OpenAI to version 1.55.3+")
                logger.error("   - Solution 2: Pin httpx to version 0.27.2")
                logger.error("   - Add this to your requirements.txt: httpx==0.27.2")
            
            raise

    def _verify_client_connection(self, client):
        """Verify that the client can connect to Perplexity API"""
        try:
            logger.info("🔍 Verifying client connection to Perplexity API...")
            
            # Make a minimal test request to verify connectivity
            test_response = client.chat.completions.create(
                model="sonar-pro",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant."
                    },
                    {
                        "role": "user", 
                        "content": "Test connection. Reply with just 'OK'."
                    }
                ],
                max_tokens=5,
                temperature=0.1,
                stream=False
            )
            
            if test_response and test_response.choices:
                logger.info(f"✅ Connection test successful: {test_response.choices[0].message.content}")
                return True
            else:
                logger.error("❌ Connection test failed: No response received")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection verification failed: {e}")
            
            # Provide detailed error analysis
            if "401" in str(e) or "Unauthorized" in str(e):
                logger.error("🔍 DIAGNOSIS: API Key Authentication Error")
                logger.error("   - Check if your PERPLEXITY_API_KEY is correct")
                logger.error("   - Verify the API key hasn't expired")
                logger.error("   - Ensure you have sufficient credits")
            elif "404" in str(e) or "Not Found" in str(e):
                logger.error("🔍 DIAGNOSIS: Model or Endpoint Error")
                logger.error("   - The specified model might not be available")
                logger.error("   - Check if the base_url is correct")
            elif "timeout" in str(e).lower():
                logger.error("🔍 DIAGNOSIS: Network Timeout")
                logger.error("   - Check your internet connection")
                logger.error("   - Try again in a few moments")
            else:
                logger.error(f"🔍 DIAGNOSIS: Unknown Error - {type(e).__name__}: {e}")
                
            return False

    def diagnose_environment(self):
        """Perform comprehensive environment diagnostics"""
        logger.info("🩺 Performing environment diagnostics...")
        
        # Check Python version
        python_version = sys.version_info
        logger.info(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check OpenAI library version
        try:
            import openai
            logger.info(f"🤖 OpenAI library version: {openai.__version__}")
            
            # Check if version is compatible
            version_parts = openai.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            
            if major == 1 and minor < 55:
                logger.warning("⚠️  OpenAI library version may be incompatible")
                logger.warning("   Consider updating to version 1.55.3 or later")
        except Exception as e:
            logger.error(f"❌ Could not determine OpenAI version: {e}")
        
        # Check httpx version if available
        try:
            import httpx
            logger.info(f"🌐 httpx version: {httpx.__version__}")
            
            # Check if httpx version is problematic
            version_parts = httpx.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            
            if major == 0 and minor >= 28:
                logger.warning("⚠️  httpx version 0.28+ may cause 'proxies' errors")
                logger.warning("   Consider downgrading to httpx==0.27.2")
        except Exception as e:
            logger.info("ℹ️  httpx version could not be determined")
        
        # Check environment variables
        env_vars = ['PERPLEXITY_API_KEY', 'OPENAI_API_KEY', 'PYTHONIOENCODING']
        for var in env_vars:
            value = os.getenv(var)
            if value:
                masked_value = f"{value[:5]}***" if len(value) > 5 else "***"
                logger.info(f"🔐 {var}: {masked_value}")
            else:
                logger.info(f"🔐 {var}: Not set")

    def read_portfolio_summary(self, file_path="exports/portfolio_summary.txt"):
        """Read the portfolio summary from the specified file"""
        try:
            logger.info(f"📁 Reading portfolio summary from {file_path}")
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"✅ Successfully loaded portfolio summary")
            logger.info(f"📄 Content length: {len(content)} characters")
            return content
        except FileNotFoundError:
            logger.error(f"❌ Error: Could not find {file_path}")
            logger.error("Make sure your portfolio analyzer has generated the summary file.")
            return None
        except Exception as e:
            logger.error(f"❌ Error reading file: {e}")
            return None

    def analyze_with_perplexity(self, portfolio_content, custom_prompt=None):
        """Send portfolio content to Perplexity API for analysis"""
        if custom_prompt is None:
            prompt = "Summarize this content in 100 lines"
        else:
            prompt = custom_prompt

        try:
            logger.info("🔄 Sending request to Perplexity API...")
            logger.info(f"📝 Using model: sonar-deep-research")

            full_prompt = f"""
{prompt}

Portfolio Summary to Analyze:
{portfolio_content}
"""

            response = self.client.chat.completions.create(
                model="sonar-deep-research",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial advisor AI assistant. Analyze the portfolio data and provide insights based on current market conditions and best practices."
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.1,
                stream=False
            )

            if response and response.choices:
                logger.info("✅ Successfully received response from Perplexity API")
                return response.choices[0].message.content
            else:
                logger.error("❌ Received empty response from API")
                return None

        except Exception as e:
            logger.error(f"❌ Error calling Perplexity API: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return None

    def save_analysis(self, analysis_content, filename=None):
        """Save the analysis result to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/portfolio_analysis_{timestamp}.txt"

        try:
            os.makedirs('exports', exist_ok=True)
            
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f"Portfolio Analysis Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
                file.write("="*80 + "\\n\\n")
                file.write(analysis_content)

            logger.info(f"💾 Analysis saved to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"❌ Error saving analysis: {e}")
            return None

def main():
    """Main function to orchestrate the portfolio analysis"""
    logger.info("🚀 Enhanced Perplexity Portfolio Analyzer")
    logger.info("=" * 50)

    try:
        # Initialize analyzer with verification
        analyzer = PerplexityAnalyzer()
        
        # Perform environment diagnostics
        analyzer.diagnose_environment()

        # Read portfolio summary
        portfolio_summary = analyzer.read_portfolio_summary()
        if not portfolio_summary:
            logger.error("❌ Cannot proceed without portfolio summary")
            return

        # Perform analysis
        logger.info("🤖 Starting portfolio analysis...")
        analysis = analyzer.analyze_with_perplexity(portfolio_summary, "")

        if analysis:
            logger.info("\\n" + "="*80)
            logger.info("🎯 PERPLEXITY AI ANALYSIS RESULT")
            logger.info("="*80)
            print(analysis)
            logger.info("="*80)

            # Save analysis
            saved_file = analyzer.save_analysis(analysis)
            if saved_file:
                logger.info("✅ Analysis complete and saved successfully!")
            else:
                logger.warning("⚠️  Analysis complete but saving failed")
        else:
            logger.error("❌ Failed to get analysis from Perplexity API")

    except KeyboardInterrupt:
        logger.info("\\n\\n👋 Analysis interrupted by user.")
    except Exception as e:
        logger.error(f"\\n❌ Analysis failed: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Print troubleshooting guide
        logger.info("\\n🔧 TROUBLESHOOTING GUIDE:")
        logger.info("1. Update your requirements.txt with compatible versions:")
        logger.info("   openai>=1.55.3")
        logger.info("   httpx==0.27.2")
        logger.info("2. Reinstall dependencies: pip install -r requirements.txt --force-reinstall")
        logger.info("3. Verify your PERPLEXITY_API_KEY is correct")
        logger.info("4. Check your internet connection")

if __name__ == "__main__":
    main()