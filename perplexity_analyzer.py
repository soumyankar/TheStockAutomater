#!/usr/bin/env python3

"""
Perplexity Portfolio Summary Analyzer
====================================

This script reads a portfolio summary from the exports/ directory and sends it to 
Perplexity's o3 reasoning model for analysis and summarization.

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
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PerplexityAnalyzer:
    def __init__(self):
        """Initialize the Perplexity analyzer with API credentials"""
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        print(f"🔐 Loaded API Key: {self.api_key[:5]}***")

        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY environment variable not found!")

        # Configure OpenAI client to use Perplexity API
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.perplexity.ai"
        )

    def read_portfolio_summary(self, file_path="exports/portfolio_summary.txt"):
        """Read the portfolio summary from the specified file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            print(f"✅ Successfully loaded portfolio summary from {file_path}")
            print(f"📄 Content length: {len(content)} characters")
            return content
        except FileNotFoundError:
            print(f"❌ Error: Could not find {file_path}")
            print("Make sure your portfolio analyzer has generated the summary file.")
            return None
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None

    def analyze_with_o3(self, portfolio_content, custom_prompt=None):
        """Send portfolio content to Perplexity's o3 reasoning model"""

        if custom_prompt is None:
            prompt = "Summarize this content in 100 lines"
        else:
            prompt = custom_prompt

        try:
            print("🔄 Sending request to Perplexity o3 reasoning model...")
            print(f"📝 Prompt: {prompt}")

            # Create the full prompt with context
            full_prompt = f"""
{prompt}

Portfolio Summary to Analyze:
{portfolio_content}
"""

            response = self.client.chat.completions.create(
                model="o3-mini",  # Using o3-mini as it's available in reasoning mode
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a financial advisor AI assistant specializing in portfolio analysis. Provide clear, concise, and actionable insights."
                    },
                    {
                        "role": "user", 
                        "content": full_prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.1,  # Lower temperature for more focused analysis
                stream=False
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"❌ Error calling Perplexity API: {e}")
            return None

    def analyze_with_reasoning_mode(self, portfolio_content, custom_prompt=None):
        """Send portfolio content using Perplexity's sonar-reasoning model"""

        if custom_prompt is None:
            prompt = "Summarize this content in 100 lines"
        else:
            prompt = custom_prompt

        try:
            print("🔄 Sending request to Perplexity sonar-reasoning model...")
            print(f"📝 Prompt: {prompt}")

            full_prompt = f"""
{prompt}

Portfolio Summary to Analyze:
{portfolio_content}
"""

            response = self.client.chat.completions.create(
                # ***LINE CHANGED here to sonar-deep-research only.***
                model="sonar-deep-research",  # Using sonar-deep-research-reasoning for web search + reasoning
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

            # Change the response to only have the summary bit
            # Some data santization
            response = response.choices[0].message.content
            return response
            

        except Exception as e:
            print(f"❌ Error calling Perplexity sonar-reasoning API: {e}")
            return None

    def save_analysis(self, analysis_content, filename=None):
        """Save the analysis result to a file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"exports/portfolio_analysis_{timestamp}.txt"

        try:
            # Ensure exports directory exists
            os.makedirs('exports', exist_ok=True)

            with open(filename, 'w', encoding='utf-8') as file:
                file.write(f"Portfolio Analysis Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                file.write("="*80 + "\n\n")
                file.write(analysis_content)

            print(f"💾 Analysis saved to: {filename}")
            return filename

        except Exception as e:
            print(f"❌ Error saving analysis: {e}")
            return None

def main():
    """Main function to orchestrate the portfolio analysis"""
    print("🚀 Perplexity Portfolio Analyzer")
    print("=" * 50)

    try:
        # Initialize analyzer
        analyzer = PerplexityAnalyzer()

        # Read portfolio summary
        portfolio_summary = analyzer.read_portfolio_summary()
        if not portfolio_summary:
            return

        # Choose analysis method
        print("\n🤖 Choosing analysis method:")
        print("sonar-deep-research reasoning model (with web search)")

        choice = "2" # forcing a model

        # Defining a few custom prompts here
        print("\n📝 Using prompts:")

        custom_prompt = ""

        # Perform analysis
        if choice == "1":
            analysis = analyzer.analyze_with_o3(portfolio_summary, custom_prompt)
        elif choice == "2":
            analysis = analyzer.analyze_with_reasoning_mode(portfolio_summary, custom_prompt)
        else:
            print("❌ Invalid choice. Using o3-mini by default.")
            analysis = analyzer.analyze_with_o3(portfolio_summary, custom_prompt)

        if analysis:
            print("\n" + "="*80)
            print("🎯 PERPLEXITY AI ANALYSIS RESULT")
            print("="*80)
            print(analysis)
            print("="*80)

            # Save analysis
            analyzer.save_analysis(analysis)
            print("\n✅ Analysis complete!")
        else:
            print("❌ Failed to get analysis from Perplexity API")

    except KeyboardInterrupt:
        print("\n\n👋 Analysis interrupted by user.")
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")

if __name__ == "__main__":
    main()
