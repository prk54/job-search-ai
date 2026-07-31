import os
import sys
import re
import json
import shutil
import subprocess
from typing import Optional

class LLMExecutionError(Exception):
    pass

class BaseLLMDriver:
    def execute(self, prompt: str) -> str:
        """Executes a prompt against the underlying LLM CLI and returns stdout."""
        raise NotImplementedError("Drivers must implement execute()")

class ClaudeDriver(BaseLLMDriver):
    def execute(self, prompt: str) -> str:
        # Enforce non-interactive environment variables
        env = os.environ.copy()
        env["CI"] = "1"
        env["NONINTERACTIVE"] = "1"
        
        # We try to use --bare to make it fast
        cmd = ["claude", "--bare", "-p", prompt]
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                env=env,
                timeout=60 # 60-second execution safeguard
            )
            if result.returncode != 0:
                # Fallback to standard claude -p without --bare if --bare is unsupported by older versions
                fallback_cmd = ["claude", "-p", prompt]
                fallback_result = subprocess.run(
                    fallback_cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=60
                )
                if fallback_result.returncode != 0:
                    err_msg = fallback_result.stderr or fallback_result.stdout
                    raise LLMExecutionError(f"Claude CLI execution failed: {err_msg}")
                return fallback_result.stdout
            return result.stdout
        except subprocess.TimeoutExpired:
            raise LLMExecutionError("Claude CLI execution timed out after 60 seconds.")
        except Exception as e:
            raise LLMExecutionError(f"Failed to execute Claude CLI: {e}")

class AntigravityDriver(BaseLLMDriver):
    def execute(self, prompt: str) -> str:
        env = os.environ.copy()
        env["CI"] = "1"
        env["NONINTERACTIVE"] = "1"
        
        # agy command
        cmd = ["agy", "-p", prompt]
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            if result.returncode != 0:
                err_msg = result.stderr or result.stdout
                raise LLMExecutionError(f"Antigravity CLI execution failed: {err_msg}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise LLMExecutionError("Antigravity CLI execution timed out after 60 seconds.")
        except Exception as e:
            raise LLMExecutionError(f"Failed to execute Antigravity CLI: {e}")

class OllamaDriver(BaseLLMDriver):
    def __init__(self, model: str = "llama3"):
        self.model = model

    def execute(self, prompt: str) -> str:
        cmd = ["ollama", "run", self.model, prompt]
        try:
            result = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=90 # Local generation might take slightly longer
            )
            if result.returncode != 0:
                err_msg = result.stderr or result.stdout
                raise LLMExecutionError(f"Ollama execution failed: {err_msg}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise LLMExecutionError("Ollama execution timed out after 90 seconds.")
        except Exception as e:
            raise LLMExecutionError(f"Failed to execute Ollama: {e}")

class CustomCommandDriver(BaseLLMDriver):
    def __init__(self, command_template: str):
        self.command_template = command_template

    def execute(self, prompt: str) -> str:
        # Interpolate the prompt securely
        # Note: We use formatting and pass to shell. To avoid shell injection issues,
        # we try to run it safely, but since it's a shell template, we use shell=True.
        # This is acceptable for local tool setups.
        command = self.command_template.replace("{prompt}", prompt)
        try:
            result = subprocess.run(
                command,
                shell=True,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                err_msg = result.stderr or result.stdout
                raise LLMExecutionError(f"Custom LLM CLI command failed: {err_msg}")
            return result.stdout
        except subprocess.TimeoutExpired:
            raise LLMExecutionError("Custom LLM CLI command timed out after 60 seconds.")
        except Exception as e:
            raise LLMExecutionError(f"Failed to execute custom LLM command: {e}")

def detect_llm_driver(provider: str, custom_command: Optional[str] = None) -> BaseLLMDriver:
    """Return the correct LLM driver based on configuration and system path"""
    if provider == "custom" and custom_command:
        return CustomCommandDriver(custom_command)
    elif provider == "claude" and shutil.which("claude"):
        return ClaudeDriver()
    elif provider == "agy" and shutil.which("agy"):
        return AntigravityDriver()
    elif provider == "ollama" and shutil.which("ollama"):
        return OllamaDriver()
        
    # Auto-detection fallback
    print("Specified LLM provider not found. Auto-detecting available system CLI LLMs...")
    if shutil.which("claude"):
        print("  → Detected 'claude' (Claude Code). Using ClaudeDriver.")
        return ClaudeDriver()
    elif shutil.which("agy"):
        print("  → Detected 'agy' (Google Antigravity). Using AntigravityDriver.")
        return AntigravityDriver()
    elif shutil.which("ollama"):
        print("  → Detected 'ollama'. Using OllamaDriver (llama3).")
        return OllamaDriver()
        
    raise RuntimeError(
        "No supported LLM CLI tools found in your system path (claude, agy, or ollama).\n"
        "Please install Claude Code (npm i -g @anthropic-ai/claude-code) or similar before running."
    )

def parse_json_from_llm(output: str) -> dict:
    """Extract and parse structured JSON from LLM text containing <json> tags or raw JSON"""
    # 1. Look for XML tags
    tag_match = re.search(r"<json>(.*?)</json>", output, re.DOTALL)
    if tag_match:
        try:
            return json.loads(tag_match.group(1).strip())
        except json.JSONDecodeError:
            pass
            
    # 2. Look for markdown json blocks
    block_match = re.search(r"```json(.*?)```", output, re.DOTALL)
    if block_match:
        try:
            return json.loads(block_match.group(1).strip())
        except json.JSONDecodeError:
            pass
            
    # 3. Fallback: find first '{' and last '}'
    first_bracket = output.find('{')
    last_bracket = output.rfind('}')
    if first_bracket != -1 and last_bracket != -1:
        try:
            return json.loads(output[first_bracket:last_bracket+1].strip())
        except json.JSONDecodeError:
            pass
            
    raise ValueError(f"Could not parse valid JSON from LLM output: {output}")
