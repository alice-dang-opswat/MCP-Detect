import os
import socket
import subprocess
import sys
import pkgutil
import http.client
import json
import re

# ------------------------
# Internal MCP Detection
# ------------------------

def check_env_vars():
    return {k: v for k, v in os.environ.items() if "MCP" in k.upper()}

def check_python_packages():
    mcp_pkgs = []
    for pkg in pkgutil.iter_modules():
        if "mcp" in pkg.name.lower() or "modelcontext" in pkg.name.lower():
            mcp_pkgs.append(pkg.name)
    return mcp_pkgs

def check_running_processes_windows():
    try:
        out = subprocess.check_output(["tasklist"], text=True, errors="ignore")
        kws = ["mcp", "model-context", "copilot", "chatgpt", "claude", "gemini", "cursor", "cody", "tabnine", "codium"]
        return [line for line in out.splitlines() if any(k in line.lower() for k in kws)]
    except:
        return []

def check_running_processes_unix():
    try:
        out = subprocess.check_output(["ps", "aux"], text=True, errors="ignore")
        kws = ["mcp", "model-context", "copilot", "chatgpt", "claude", "gemini", "cursor", "cody", "tabnine", "codium"]
        return [line for line in out.splitlines() if any(k in line.lower() for k in kws)]
    except:
        return []

def check_common_directories():
    paths = [
        os.path.expanduser("~/.config/mcp"),
        os.path.expanduser("~/mcp"),
        "/usr/local/mcp",
        "C:\\Program Files\\MCP",
        "C:\\ProgramData\\MCP",
    ]
    return [p for p in paths if os.path.exists(p)]

# ------------------------
# AI Assistant Detection
# ------------------------

def check_vscode_extensions():
    """Check for AI assistant extensions in VS Code"""
    detected = []
    vscode_paths = [
        os.path.expanduser("~/.vscode/extensions"),
        os.path.expanduser("~/.vscode-insiders/extensions"),
        os.path.expanduser("~/AppData/Local/Programs/Microsoft VS Code/resources/app/extensions"),
        os.path.expanduser("~/.cursor/extensions"),
    ]
    
    ai_extensions = {
        "github.copilot": "GitHub Copilot",
        "github.copilot-chat": "GitHub Copilot Chat",
        "anthropic.claude": "Claude for VS Code",
        "googlecloudtools.cloudcode": "Google Cloud Code (includes Gemini)",
        "amazonwebservices.aws-toolkit": "AWS Toolkit (includes CodeWhisperer)",
        "tabnine.tabnine-vscode": "Tabnine",
        "sourcegraph.cody-ai": "Cody AI",
        "continue.continue": "Continue",
        "cursor.cursor": "Cursor IDE",
    }
    
    for vscode_path in vscode_paths:
        if not os.path.exists(vscode_path):
            continue
        try:
            for ext_name, display_name in ai_extensions.items():
                for item in os.listdir(vscode_path):
                    if ext_name in item.lower():
                        detected.append(f"{display_name} ({item})")
        except:
            pass
    
    return detected

def check_browser_extensions():
    """Check for AI assistant browser extensions"""
    detected = []
    
    # Chrome/Edge extension paths
    chrome_paths = [
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Extensions"),
        os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Extensions"),
        os.path.expanduser("~/AppData/Local/Microsoft/Edge/User Data/Default/Extensions"),
    ]
    
    # Known AI extension IDs
    ai_extension_ids = {
        "aapbdbdomjkkjkaonfhkkikfgjllcleb": "ChatGPT for Google",
        "ngebdfhfdjkclpjdjgeimfkleclikohe": "ChatGPT Writer",
        "jcaelnkhhhfpgpapfomgjbdmjfmkoknj": "ChatGPT for Search Engines",
        "hhfkcobomkalfdlmkongnhngjkijempf": "Copilot",
        "gfbcgkpfghcffemdncplifhmdkopmkaf": "Monica AI",
        "aiifbnbfobpmeekipheeijimdpnlpgpp": "Merlin AI",
    }
    
    for chrome_path in chrome_paths:
        if not os.path.exists(chrome_path):
            continue
        try:
            for item in os.listdir(chrome_path):
                if item in ai_extension_ids:
                    detected.append(ai_extension_ids[item])
                # Generic detection for other AI extensions
                manifest_path = os.path.join(chrome_path, item, "manifest.json")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            manifest = json.load(f)
                            name = manifest.get('name', '')
                            if any(keyword in name.lower() for keyword in ['chatgpt', 'copilot', 'claude', 'gemini', 'ai assistant', 'gpt']):
                                if name not in detected:
                                    detected.append(name)
                    except:
                        pass
        except:
            pass
    
    return detected

def check_installed_apps():
    """Check for AI assistant desktop applications"""
    detected = []
    
    # Windows Program Files
    program_paths = [
        "C:\\Program Files",
        "C:\\Program Files (x86)",
        os.path.expanduser("~/AppData/Local/Programs"),
        os.path.expanduser("~/AppData/Local"),
    ]
    
    # macOS/Linux paths
    if os.name != "nt":
        program_paths.extend([
            "/Applications",
            os.path.expanduser("~/Applications"),
            "/usr/local/bin",
        ])
    
    ai_apps = {
        "ChatGPT": "ChatGPT Desktop",
        "Claude": "Claude Desktop",
        "Cursor": "Cursor IDE",
        "Copilot": "GitHub Copilot",
        "Cody": "Sourcegraph Cody",
        "Tabnine": "Tabnine",
        "Gemini": "Google Gemini",
        "Perplexity": "Perplexity",
    }
    
    for program_path in program_paths:
        if not os.path.exists(program_path):
            continue
        try:
            for item in os.listdir(program_path):
                for app_name, display_name in ai_apps.items():
                    if app_name.lower() in item.lower():
                        detected.append(f"{display_name} ({item})")
        except:
            pass
    
    return detected

def check_ai_api_keys():
    """Check for AI API keys in environment variables"""
    detected = []
    api_key_patterns = {
        "OPENAI": "OpenAI (ChatGPT)",
        "ANTHROPIC": "Anthropic (Claude)",
        "GOOGLE_AI": "Google AI (Gemini)",
        "COHERE": "Cohere",
        "HUGGINGFACE": "Hugging Face",
        "GITHUB_COPILOT": "GitHub Copilot",
        "AWS_": "AWS (CodeWhisperer)",
        "TABNINE": "Tabnine",
    }
    
    for key, value in os.environ.items():
        for pattern, name in api_key_patterns.items():
            if pattern in key.upper() and "KEY" in key.upper():
                detected.append(f"{name} ({key})")
    
    return detected

def check_browser_processes():
    """Check for browsers accessing AI websites by examining window titles and command lines"""
    detected = []
    
    if os.name == "nt":
        # Method 1: Check window titles using PowerShell
        try:
            ps_script = '''
$code = @"
using System;
using System.Text;
using System.Runtime.InteropServices;
public class WindowHelper {
    public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
    [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
}
"@
Add-Type -TypeDefinition $code -ErrorAction SilentlyContinue
$windows = New-Object System.Collections.ArrayList
[WindowHelper]::EnumWindows({
    param($hWnd, $lParam)
    $sb = New-Object System.Text.StringBuilder 500
    [WindowHelper]::GetWindowText($hWnd, $sb, 500) | Out-Null
    $title = $sb.ToString()
    if ($title -match "ChatGPT|Claude|Gemini|Copilot|Perplexity|Poe|OpenAI|Anthropic|Bard") {
        $pid = 0
        [WindowHelper]::GetWindowThreadProcessId($hWnd, [ref]$pid) | Out-Null
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) { $windows.Add("$($proc.Name)|$title") | Out-Null }
    }
    return $true
}, [IntPtr]::Zero) | Out-Null
$windows
'''
            result = subprocess.check_output(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
                text=True,
                errors="ignore",
                timeout=5
            )
            
            ai_sites = {
                "chatgpt": "ChatGPT",
                "openai": "OpenAI",
                "claude": "Claude",
                "anthropic": "Anthropic",
                "gemini": "Google Gemini",
                "bard": "Google Bard",
                "copilot": "Copilot",
                "perplexity": "Perplexity",
                "poe": "Poe",
            }
            
            found_sites = {}
            for line in result.strip().split('\n'):
                line = line.strip()
                if line and '|' in line:
                    try:
                        process, title = line.split('|', 1)
                        title_lower = title.lower()
                        process_lower = process.lower()
                        
                        browser = "browser"
                        if "chrome" in process_lower:
                            browser = "Chrome"
                        elif "msedge" in process_lower or "edge" in process_lower:
                            browser = "Edge"
                        elif "firefox" in process_lower:
                            browser = "Firefox"
                        elif "brave" in process_lower:
                            browser = "Brave"
                        
                        for keyword, name in ai_sites.items():
                            if keyword in title_lower:
                                # Store with browser info, avoid duplicates
                                if name not in found_sites:
                                    found_sites[name] = browser
                                break
                    except:
                        pass
            
            for name, browser in found_sites.items():
                detected.append(f"✓ {name} (open in {browser})")
            
            if found_sites:
                detected.extend(sorted(found_sites))
        except:
            pass
        
        # Method 2: Check browser command lines for URLs (requires admin)
        if not detected:
            try:
                wmic_cmd = 'wmic process where "name=\'chrome.exe\' or name=\'msedge.exe\' or name=\'firefox.exe\'" get commandline /format:list'
                result = subprocess.check_output(wmic_cmd, shell=True, text=True, errors="ignore", timeout=3)
                
                ai_urls = ["chatgpt.com", "chat.openai.com", "claude.ai", "gemini.google.com", 
                          "copilot.microsoft.com", "perplexity.ai", "poe.com", "bard.google.com"]
                
                for url in ai_urls:
                    if url in result.lower():
                        site_name = url.split('.')[0].title()
                        if "chatgpt" in url or "openai" in url:
                            site_name = "ChatGPT"
                        elif "claude" in url:
                            site_name = "Claude"
                        elif "gemini" in url or "bard" in url:
                            site_name = "Google Gemini"
                        detected.add(f"✓ {site_name} (detected in browser)")
            except:
                pass
        
        # Fallback: just show browsers running
        if not detected:
            try:
                browsers_found = []
                out = subprocess.check_output(["tasklist"], text=True, errors="ignore")
                if "chrome.exe" in out.lower():
                    browsers_found.append("Chrome")
                if "msedge.exe" in out.lower():
                    browsers_found.append("Edge")
                if "firefox.exe" in out.lower():
                    browsers_found.append("Firefox")
                
                if browsers_found:
                    detected.append(f"Browser(s) running: {', '.join(browsers_found)} (unable to detect specific AI sites)")
            except:
                pass
    else:
        # Unix/Linux/macOS - simplified
        try:
            out = subprocess.check_output(["ps", "aux"], text=True, errors="ignore")
            browsers = []
            if "chrome" in out.lower():
                browsers.append("Chrome")
            if "firefox" in out.lower():
                browsers.append("Firefox")
            if "safari" in out.lower():
                browsers.append("Safari")
            if browsers:
                detected.append(f"Browser(s) running: {', '.join(browsers)}")
        except:
            pass
    
    return detected

def check_browser_history():
    """Check browser history for AI website visits"""
    detected = []
    
    ai_websites = {
        "chatgpt.com": "ChatGPT",
        "chat.openai.com": "ChatGPT",
        "claude.ai": "Claude",
        "gemini.google.com": "Google Gemini",
        "bard.google.com": "Google Bard",
        "copilot.microsoft.com": "Microsoft Copilot",
        "bing.com/chat": "Bing Chat",
        "perplexity.ai": "Perplexity",
        "poe.com": "Poe",
        "you.com": "You.com AI",
    }
    
    # Chrome history locations
    chrome_history_paths = [
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/History"),
        os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/History"),
        os.path.expanduser("~/.config/google-chrome/Default/History"),
    ]
    
    # Check for existence of history files (don't read them as they may be locked)
    # Instead, check cache and temp files
    chrome_cache_paths = [
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Cache"),
        os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Code Cache"),
    ]
    
    for cache_path in chrome_cache_paths:
        if os.path.exists(cache_path):
            try:
                # Check cache directory for AI-related files (quick scan)
                for root, dirs, files in os.walk(cache_path):
                    for file in files[:50]:  # Limit to first 50 files for performance
                        file_lower = file.lower()
                        if any(domain.replace(".", "") in file_lower for domain in ai_websites.keys()):
                            domain = next((d for d in ai_websites.keys() if d.replace(".", "") in file_lower), None)
                            if domain and ai_websites[domain] not in detected:
                                detected.append(f"{ai_websites[domain]} (recent browser activity)")
                    break  # Only check first directory level
            except:
                pass
    
    return detected

# ------------------------
# MCP Server Scan
# ------------------------

COMMON_PORTS = list(range(8000, 9000))

MCP_ENDPOINTS = [
    "/health",
    "/status",
    "/mcp",
    "/v1/mcp",
    "/api/mcp",
    "/model-context",
]


def port_open(port):
    """Check if a port is listening on localhost"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.25)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        return result == 0
    except:
        return False


def check_http_endpoint(port, path):
    """Try HTTP GET on a specific endpoint."""
    try:
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=0.3)
        conn.request("GET", path)
        resp = conn.getresponse()
        data = resp.read().decode(errors="ignore")
        return resp.status, data
    except:
        return None, None


def scan_for_mcp_servers():
    detected = []

    print("\n🔍 Scanning localhost ports (8000–8999) for MCP servers...")

    for port in COMMON_PORTS:
        if not port_open(port):
            continue  # Skip closed ports

        for endpoint in MCP_ENDPOINTS:
            status, body = check_http_endpoint(port, endpoint)
            if status is None:
                continue

            # Heuristic detection of MCP-like behavior
            if any(keyword in (body or "").lower() for keyword in [
                "mcp", "model", "protocol", "context", "llm", "server"
            ]):
                detected.append({
                    "port": port,
                    "endpoint": endpoint,
                    "status": status,
                    "body": body[:200]  # show a snippet
                })
                break

    return detected

# ------------------------
# Main
# ------------------------

def main():
    print("🔍 Detecting Model Context Protocol (MCP) and AI Assistants...\n")
    print("=" * 70)

    # MCP Detection
    env = check_env_vars()
    py = check_python_packages()
    dirs = check_common_directories()

    if os.name == "nt":
        procs = check_running_processes_windows()
    else:
        procs = check_running_processes_unix()

    print("\n📋 MODEL CONTEXT PROTOCOL (MCP) DETECTION")
    print("=" * 70)
    
    print("\n=== Environment Variables ===")
    print(env if env else "❌ No MCP environment variables found.")

    print("\n=== Python Packages ===")
    print(py if py else "❌ No MCP-related Python packages found.")

    print("\n=== Running Processes ===")
    if procs:
        for proc in procs:
            print(f"  • {proc}")
    else:
        print("❌ No MCP/AI-related processes detected.")

    print("\n=== MCP Directories ===")
    if dirs:
        for d in dirs:
            print(f"  • {d}")
    else:
        print("❌ No MCP installation directories detected.")

    # --- External MCP Server Scan ---
    servers = scan_for_mcp_servers()
    print("\n=== Local MCP Server Scan ===")
    if servers:
        for s in servers:
            print(f"✅ MCP-like server detected on port {s['port']} (endpoint {s['endpoint']})")
            print(f"   Response snippet: {s['body']}\n")
    else:
        print("❌ No MCP servers detected on localhost ports 8000–8999.")

    # AI Assistant Detection
    print("\n" + "=" * 70)
    print("🤖 AI ASSISTANT DETECTION")
    print("=" * 70)
    
    vscode_exts = check_vscode_extensions()
    print("\n=== VS Code / IDE Extensions ===")
    if vscode_exts:
        for ext in vscode_exts:
            print(f"  ✅ {ext}")
    else:
        print("❌ No AI assistant IDE extensions detected.")
    
    browser_exts = check_browser_extensions()
    print("\n=== Browser Extensions ===")
    if browser_exts:
        for ext in browser_exts:
            print(f"  ✅ {ext}")
    else:
        print("❌ No AI assistant browser extensions detected.")
    
    browser_procs = check_browser_processes()
    print("\n=== Active AI Websites in Browser ===")
    if browser_procs:
        for proc in browser_procs:
            print(f"  ✅ {proc}")
    else:
        print("❌ No AI websites currently detected in browser windows.")
    
    browser_hist = check_browser_history()
    print("\n=== Recent AI Website Activity ===")
    if browser_hist:
        for hist in browser_hist:
            print(f"  ✅ {hist}")
    else:
        print("❌ No recent AI website activity detected in browser cache.")
    
    apps = check_installed_apps()
    print("\n=== Desktop Applications ===")
    if apps:
        for app in apps:
            print(f"  ✅ {app}")
    else:
        print("❌ No AI assistant desktop applications detected.")
    
    api_keys = check_ai_api_keys()
    print("\n=== AI API Keys (Environment Variables) ===")
    if api_keys:
        for key in api_keys:
            print(f"  ✅ {key}")
    else:
        print("❌ No AI API keys found in environment variables.")

    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    mcp_detected = bool(env or py or procs or dirs or servers)
    ai_detected = bool(vscode_exts or browser_exts or browser_procs or browser_hist or apps or api_keys)
    
    if mcp_detected:
        print("✅ Model Context Protocol (MCP) components detected")
    else:
        print("❌ No MCP components found")
    
    if ai_detected:
        print("✅ AI Assistants detected")
        print(f"   - IDE Extensions: {len(vscode_exts)}")
        print(f"   - Browser Extensions: {len(browser_exts)}")
        print(f"   - Active AI Websites: {len(browser_procs)}")
        print(f"   - Recent AI Website Activity: {len(browser_hist)}")
        print(f"   - Desktop Apps: {len(apps)}")
        print(f"   - API Keys: {len(api_keys)}")
    else:
        print("❌ No AI assistants found")
    
    if not mcp_detected and not ai_detected:
        print("\n⚠️  No MCP or AI assistant components detected on this system.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
