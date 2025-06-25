#!/usr/bin/env python3

import psutil
import platform
import os

def check_system_specs():
    """Check system specifications and recommend Ollama models"""
    
    print("🖥️  System Specifications Check")
    print("=" * 50)
    
    # RAM
    ram_gb = psutil.virtual_memory().total / (1024**3)
    print(f"📊 RAM: {ram_gb:.1f} GB")
    
    # CPU
    cpu_count = psutil.cpu_count()
    cpu_freq = psutil.cpu_freq()
    print(f"🖥️  CPU: {cpu_count} cores")
    if cpu_freq:
        print(f"    Frequency: {cpu_freq.current:.0f} MHz")
    
    # Storage
    disk = psutil.disk_usage('/')
    disk_gb = disk.free / (1024**3)
    print(f"💾 Free Storage: {disk_gb:.1f} GB")
    
    # OS
    print(f"🪟 OS: {platform.system()} {platform.release()}")
    
    print("\n🎯 Ollama Model Recommendations:")
    print("=" * 50)
    
    # Recommendations based on RAM
    if ram_gb >= 32:
        print("✅ HIGH-END SYSTEM - All models recommended:")
        print("   • Llama2 13B (Best quality)")
        print("   • CodeLlama 13B (Technical topics)")
        print("   • Mistral 7B (Fast and good)")
        print("   • Phi-2 (Lightning fast)")
        
    elif ram_gb >= 16:
        print("✅ MID-RANGE SYSTEM - Most models work well:")
        print("   • Llama2 7B (Good quality)")
        print("   • CodeLlama 7B (Technical topics)")
        print("   • Mistral 7B (Fast and good)")
        print("   • Phi-2 (Lightning fast)")
        
    elif ram_gb >= 8:
        print("✅ STANDARD SYSTEM - Smaller models recommended:")
        print("   • Phi-2 (Best choice - fast and efficient)")
        print("   • Mistral 7B (Good quality, moderate speed)")
        print("   • Llama2 7B (Good quality, slower)")
        
    else:
        print("⚠️  LIMITED SYSTEM - Consider these options:")
        print("   • Phi-2 (Only recommended option)")
        print("   • Or use template-based responses (no LLM)")
        print("   • Or consider cloud APIs (Gemini, OpenAI)")
    
    print("\n💡 Performance Tips:")
    print("=" * 50)
    
    if ram_gb < 16:
        print("• Close other applications when using Ollama")
        print("• Start with Phi-2 model for best performance")
        print("• Consider upgrading RAM if possible")
    
    if disk_gb < 10:
        print("• Free up disk space before installing models")
        print("• Models require 2-8GB each")
    
    print("\n🚀 Quick Start Commands:")
    print("=" * 50)
    print("1. Install Ollama: https://ollama.ai")
    print("2. Start service: ollama serve")
    print("3. Download model: ollama pull phi-2")
    print("4. Test: ollama run phi-2 'Hello!'")
    
    print("\n📊 Expected Performance:")
    print("=" * 50)
    
    if ram_gb >= 16:
        print("• Response time: 2-5 seconds")
        print("• Quality: Excellent")
        print("• Can run multiple models")
    elif ram_gb >= 8:
        print("• Response time: 3-8 seconds")
        print("• Quality: Good")
        print("• Best with Phi-2 or Mistral")
    else:
        print("• Response time: 5-15 seconds")
        print("• Quality: Acceptable")
        print("• Only Phi-2 recommended")

if __name__ == "__main__":
    try:
        check_system_specs()
    except Exception as e:
        print(f"Error checking system specs: {e}")
        print("\n💡 Manual Check:")
        print("• Right-click Start → System")
        print("• Look for 'Installed RAM'")
        print("• 8GB+ = Good for Ollama")
        print("• 16GB+ = Excellent for Ollama") 