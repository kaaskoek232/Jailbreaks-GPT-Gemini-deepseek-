import datetime

def log_agent_action(message, log_file="agent_action_log_001.md"):
    """
    Append a compact, timestamped diary entry to the agent action log.
    Only use for high-level actions, decisions, or batch summaries.
    """
    timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    entry = f"{timestamp} {message}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)

def log_dev_context_bridge():
    """
    Log a bridging entry summarizing the current dev and context level for a new chat instance.
    """
    summary = (
        "Bridging context: Unified MCP Agent System is fully integrated with Cursor tool validation, "
        "modular LLM support (Ollama, Gemini, OpenAI), context-aware agent, Tkinter UI, persistent memory, "
        "and diary-style agent action log. Current focus: robust agent lifecycle, meaningful logging, and "
        "efficient batch operations. Awaiting further deployment and post-deploy tuning."
    )
    log_agent_action(summary)

# Immediately log the bridge entry for the next chat instance
log_dev_context_bridge() 