# Create the fixed automation script
# fixed_script = '''#!/usr/bin/env python3
"""
Portfolio Automation Script - Fixed Version
Automates the execution of portfolio analysis workflow with proper encoding handling
"""


import subprocess
import logging
import sys
import time
import os
from datetime import datetime
from pathlib import Path

class WorkflowAutomator:
    """
    Orchestrates the execution of multiple Python scripts in sequence
    with comprehensive logging and error handling.
    """

    def __init__(self, log_level=logging.INFO):
        """Initialize the automator with logging configuration."""
        self.setup_logging(log_level)
        self.scripts = [
            "portfolio_analyzer.py",
            "perplexity_analyzer.py", 
            "portfolio_notifier.py"
        ]
        self.script_descriptions = {
            "portfolio_analyzer.py": "Portfolio data processing and summary generation",
            "perplexity_analyzer.py": "AI analysis via Perplexity API",
            "portfolio_notifier.py": "Telegram notification delivery"
        }
        
        # Set environment for UTF-8 encoding
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'

    def setup_logging(self, log_level):
        """Configure logging with both file and console output."""
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Generate timestamped log filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"workflow_automation_{timestamp}.log"

        # Configure logging format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Workflow automation initialized. Log file: {log_file}")

    def validate_script_exists(self, script_name):
        """Check if a script file exists before attempting to run it."""
        if not Path(script_name).exists():
            self.logger.error(f"Script not found: {script_name}")
            return False
        return True

    def run_script(self, script_name, timeout=300):
        """
        Execute a Python script with comprehensive error handling and proper encoding.
        """
        if not self.validate_script_exists(script_name):
            return False

        description = self.script_descriptions.get(script_name, script_name)
        self.logger.info(f"Starting execution: {description}")
        self.logger.info(f"Command: python {script_name}")

        try:
            # Start the subprocess with explicit UTF-8 encoding
            process = subprocess.Popen(
                [sys.executable, script_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8',  # Explicit UTF-8 encoding
                errors='replace',  # Replace invalid characters instead of failing
                universal_newlines=True,
                bufsize=1
            )

            self.logger.info(f"Process started with PID: {process.pid}")

            # Wait for process completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                self.logger.error(f"Script {script_name} timed out after {timeout} seconds")
                process.kill()
                stdout, stderr = process.communicate()
                return False

            # Check return code
            return_code = process.returncode

            if return_code == 0:
                self.logger.info(f"✅ {script_name} completed successfully")
                if stdout and stdout.strip():
                    self.logger.info(f"Output: {stdout.strip()}")
                return True
            else:
                self.logger.error(f"❌ {script_name} failed with return code: {return_code}")
                if stderr and stderr.strip():
                    self.logger.error(f"Error output: {stderr.strip()}")
                if stdout and stdout.strip():
                    self.logger.info(f"Standard output: {stdout.strip()}")
                return False

        except FileNotFoundError:
            self.logger.error(f"Python interpreter or script not found: {script_name}")
            return False
        except UnicodeDecodeError as e:
            self.logger.error(f"Encoding error running {script_name}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error running {script_name}: {str(e)}")
            return False

    def wait_for_completion(self, script_name, max_wait_time=10):
        """Wait for script to complete file operations."""
        self.logger.info(f"Waiting for {script_name} to complete file operations...")
        time.sleep(max_wait_time)
        self.logger.info("Wait period completed")

    def run_workflow(self, continue_on_failure=False):
        """Execute the complete workflow in sequence."""
        self.logger.info("=" * 60)
        self.logger.info("STARTING PORTFOLIO AUTOMATION WORKFLOW")
        self.logger.info("=" * 60)

        workflow_start_time = time.time()
        results = {}

        for i, script in enumerate(self.scripts, 1):
            step_start_time = time.time()

            self.logger.info(f"\\n📋 STEP {i}/{len(self.scripts)}: {script}")
            self.logger.info("-" * 40)

            # Execute the script
            success = self.run_script(script)
            results[script] = success

            step_duration = time.time() - step_start_time
            self.logger.info(f"Step {i} duration: {step_duration:.2f} seconds")

            if success:
                # Wait for script to complete file operations
                self.wait_for_completion(script, max_wait_time=5)
            else:
                if continue_on_failure:
                    self.logger.warning(f"Continuing workflow despite {script} failure")
                else:
                    self.logger.error(f"Stopping workflow due to {script} failure")
                    break

            # Brief pause between scripts
            if i < len(self.scripts):
                self.logger.info("Pausing before next step...")
                time.sleep(2)

        # Workflow summary
        total_duration = time.time() - workflow_start_time
        self.logger.info("\\n" + "=" * 60)
        self.logger.info("WORKFLOW SUMMARY")
        self.logger.info("=" * 60)

        successful_scripts = sum(results.values())
        total_scripts = len(self.scripts)

        for script, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            self.logger.info(f"{script}: {status}")

        self.logger.info(f"\\nTotal execution time: {total_duration:.2f} seconds")
        self.logger.info(f"Success rate: {successful_scripts}/{total_scripts} scripts")

        if successful_scripts == total_scripts:
            self.logger.info("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
        else:
            self.logger.warning(f"⚠️ WORKFLOW COMPLETED WITH {total_scripts - successful_scripts} FAILURES")

        return results

def main():
    """Main entry point for the automation script."""
    print("Portfolio Workflow Automation")
    print("=" * 40)

    # Initialize automator
    automator = WorkflowAutomator(log_level=logging.INFO)

    try:
        # Run the complete workflow
        results = automator.run_workflow(continue_on_failure=False)

        # Exit with appropriate code
        if all(results.values()):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

    except KeyboardInterrupt:
        automator.logger.warning("Workflow interrupted by user")
        sys.exit(130)  # Interrupted
    except Exception as e:
        automator.logger.error(f"Unexpected error in main workflow: {str(e)}")
        sys.exit(1)  # Error

if __name__ == "__main__":
    main()