import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import json
from datetime import datetime
import queue
import os
import model_validation
from llm_integration import llm_manager

class CanvasLabelFrame(tk.Frame):
    def __init__(self, parent, text="", border_color="#444444", bg="#101010", fg="#FFFFFF", accent="#00FF41", borderwidth=2, label_green=False, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.border_color = border_color
        self.bg = bg
        self.fg = fg
        self.accent = accent
        self.borderwidth = borderwidth
        self.text = text
        self.label_green = label_green
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.inner_frame = tk.Frame(self.canvas, bg=bg)
        self.window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.canvas.bind("<Configure>", self._draw_border)
        self._draw_border()

    def _draw_border(self, event=None):
        self.canvas.delete("border")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 2 or h < 2:
            return
        # Draw border rectangle (always soft grey)
        self.canvas.create_rectangle(
            self.borderwidth, 18, w - self.borderwidth, h - self.borderwidth,
            outline="#444444", width=self.borderwidth, tags="border"
        )
        # Draw label background
        label_w = self.canvas.create_rectangle(
            10, 0, 10 + len(self.text) * 8 + 10, 22,
            fill=self.bg, outline="", tags="border"
        )
        # Draw label text (green only for header, else white)
        label_color = self.accent if self.label_green else self.fg
        self.canvas.create_text(
            20, 10, text=self.text, anchor="w", fill=label_color, font=("Fira Mono", 10, "bold"), tags="border"
        )

    def get_inner_frame(self):
        return self.inner_frame

class UnifiedAgentUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified MCP Agent System Dashboard")
        self.root.geometry("1200x800")
        self.running = True
        # Theme colors (must be set before setup_ui)
        self.bg_dark = '#101010'
        self.fg_light = '#E0FFE0'
        self.accent_green = '#00FF41'
        self.terminal_bg = self.bg_dark
        self.terminal_fg = self.fg_light
        self.accent = self.accent_green
        self.outline_grey = '#444444'
        self.setup_ui()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        # --- Matrix theme: all text white except header, all borders soft grey ---
        style.configure('.', background=self.bg_dark, foreground='#FFFFFF', font=('Fira Mono', 11))
        style.configure('TNotebook', background=self.bg_dark, foreground='#FFFFFF', borderwidth=0)
        style.configure('TNotebook.Tab', background=self.bg_dark, foreground='#FFFFFF', borderwidth=2, lightcolor=self.outline_grey, bordercolor=self.outline_grey, font=('Fira Mono', 11, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', self.bg_dark)], foreground=[('selected', self.accent)], bordercolor=[('selected', self.accent)])
        style.configure('TFrame', background=self.bg_dark, borderwidth=0, relief='flat')
        style.configure('TLabel', background=self.bg_dark, foreground='#FFFFFF', font=('Fira Mono', 11))
        style.configure('TButton', background=self.bg_dark, foreground='#FFFFFF', borderwidth=1, highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11, 'bold'))
        style.map('TButton', background=[('active', self.accent)], foreground=[('active', self.bg_dark)], highlightcolor=[('active', self.accent)])
        style.configure('TLabelframe', background=self.bg_dark, foreground='#FFFFFF', borderwidth=0, relief='flat')
        style.configure('TLabelframe.Label', background=self.bg_dark, foreground='#FFFFFF', font=('Fira Mono', 11, 'bold'))
        style.configure('TEntry', fieldbackground=self.bg_dark, foreground='#FFFFFF', borderwidth=1, highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11))
        style.configure('TCombobox', fieldbackground=self.bg_dark, foreground='#FFFFFF', background=self.bg_dark, borderwidth=1, highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11))
        style.configure('TCheckbutton', background=self.bg_dark, foreground='#FFFFFF', highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11))
        style.configure('TRadiobutton', background=self.bg_dark, foreground='#FFFFFF', highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11))
        style.configure('TSpinbox', fieldbackground=self.bg_dark, foreground='#FFFFFF', background=self.bg_dark, borderwidth=1, highlightbackground=self.outline_grey, highlightcolor=self.accent, font=('Fira Mono', 11))
        # Set root background
        self.root.configure(bg=self.bg_dark)
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        # --- Header: matrix green, rest white ---
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(title_frame, text="UNIFIED MCP AGENT SYSTEM", font=('Fira Mono', 20, 'bold'), foreground=self.accent, background=self.bg_dark).pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(title_frame, text="[Matrix Ops Dashboard]", font=('Fira Mono', 14, 'italic'), foreground='#FFFFFF', background=self.bg_dark).pack(side=tk.LEFT)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create all tabs
        self.setup_dashboard_tab()
        self.setup_connection_tab()
        self.setup_memory_tab()
        self.setup_search_tab()
        self.setup_feedback_tab()
        self.setup_heartbeat_tab()
        self.setup_ai_agent_tab()
        self.setup_conversation_tab()
        self.setup_logs_tab()
        
        # Initialize systems
        self.initialize_heartbeat_system()
        self.start_monitoring()
        # Add status bar at the bottom
        self.status_bar = tk.Label(self.root, text="Ready.", anchor='w', bg=self.bg_dark, fg=self.accent, font=('Fira Mono', 10))
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM, ipady=2)

    def setup_dashboard_tab(self):
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        status_frame = CanvasLabelFrame(dashboard_frame, text="System Status", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        status_frame.pack(fill=tk.X, pady=(0, 16), padx=8)
        self.connection_status = tk.StringVar(value="Detecting...")
        status_inner = status_frame.get_inner_frame()
        status_label_row = tk.Frame(status_inner, bg=self.bg_dark)
        status_label_row.pack(fill=tk.X, pady=(0, 4))
        ttk.Label(status_label_row, text="Connection:").pack(side=tk.LEFT, padx=(0, 12))
        ttk.Label(status_label_row, textvariable=self.connection_status, style='Status.TLabel').pack(side=tk.LEFT)
        log_buttons_frame = tk.Frame(status_inner, bg=self.bg_dark)
        log_buttons_frame.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(log_buttons_frame, text="View Current Log", command=self.load_context_from_log).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(log_buttons_frame, text="View All Logs", command=self.view_all_logs).pack(side=tk.LEFT, padx=(0, 8))
        log_frame = CanvasLabelFrame(dashboard_frame, text="Activity Log", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.activity_log = scrolledtext.ScrolledText(log_frame.get_inner_frame(), height=10, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.activity_log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.log_activity("Dashboard initialized.")

    def setup_connection_tab(self):
        connection_frame = ttk.Frame(self.notebook)
        self.notebook.add(connection_frame, text="Connection")
        settings_frame = CanvasLabelFrame(connection_frame, text="Connection Settings", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        settings_frame.pack(fill=tk.X, pady=(0, 16), padx=8)
        settings_inner = settings_frame.get_inner_frame()
        row1 = tk.Frame(settings_inner, bg=self.bg_dark)
        row1.pack(fill=tk.X, pady=4)
        ttk.Label(row1, text="Connection Type:").pack(side=tk.LEFT, padx=(0, 12))
        self.connection_type = tk.StringVar(value="local")
        connection_combo = ttk.Combobox(row1, textvariable=self.connection_type, values=["local", "ssh", "runpod"], state="readonly")
        connection_combo.pack(side=tk.LEFT)
        # SSH fields
        ssh_row = tk.Frame(settings_inner, bg=self.bg_dark)
        ssh_row.pack(fill=tk.X, pady=4)
        ttk.Label(ssh_row, text="SSH Host:").pack(side=tk.LEFT, padx=(0, 12))
        self.ssh_host = tk.StringVar()
        ttk.Entry(ssh_row, textvariable=self.ssh_host, width=20).pack(side=tk.LEFT)
        ssh_user_row = tk.Frame(settings_inner, bg=self.bg_dark)
        ssh_user_row.pack(fill=tk.X, pady=4)
        ttk.Label(ssh_user_row, text="SSH User:").pack(side=tk.LEFT, padx=(0, 12))
        self.ssh_user = tk.StringVar()
        ttk.Entry(ssh_user_row, textvariable=self.ssh_user, width=20).pack(side=tk.LEFT)
        # RunPod fields
        runpod_row = tk.Frame(settings_inner, bg=self.bg_dark)
        runpod_row.pack(fill=tk.X, pady=4)
        ttk.Label(runpod_row, text="RunPod Pod ID:").pack(side=tk.LEFT, padx=(0, 12))
        self.runpod_pod_id = tk.StringVar()
        ttk.Entry(runpod_row, textvariable=self.runpod_pod_id, width=20).pack(side=tk.LEFT)
        actions_frame = ttk.Frame(connection_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(actions_frame, text="Connect", command=lambda: self.log_activity("Connect pressed")).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(actions_frame, text="Disconnect", command=lambda: self.log_activity("Disconnect pressed")).pack(side=tk.LEFT, padx=(0, 8))

    def setup_memory_tab(self):
        memory_frame = ttk.Frame(self.notebook)
        self.notebook.add(memory_frame, text="Memory")
        operations_frame = CanvasLabelFrame(memory_frame, text="Memory Operations", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        operations_frame.pack(fill=tk.X, pady=(0, 10))
        # Store memory
        store_frame = ttk.Frame(operations_frame)
        store_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(store_frame, text="Key:").pack(side=tk.LEFT)
        self.memory_key = tk.StringVar()
        ttk.Entry(store_frame, textvariable=self.memory_key, width=15).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(store_frame, text="Value:").pack(side=tk.LEFT)
        self.memory_value = tk.StringVar()
        ttk.Entry(store_frame, textvariable=self.memory_value, width=30).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(store_frame, text="Store", command=lambda: self.log_activity("Store memory pressed")).pack(side=tk.LEFT, padx=(5, 0))
        # Retrieve memory
        retrieve_frame = ttk.Frame(operations_frame)
        retrieve_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(retrieve_frame, text="Key:").pack(side=tk.LEFT)
        self.retrieve_key = tk.StringVar()
        ttk.Entry(retrieve_frame, textvariable=self.retrieve_key, width=15).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(retrieve_frame, text="Retrieve", command=lambda: self.log_activity("Retrieve memory pressed")).pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(retrieve_frame, text="List All", command=lambda: self.log_activity("List memory pressed")).pack(side=tk.LEFT, padx=(5, 0))
        # Memory display
        display_frame = CanvasLabelFrame(memory_frame, text="Memory Contents", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        display_frame.pack(fill=tk.BOTH, expand=True)
        self.memory_display = scrolledtext.ScrolledText(display_frame.get_inner_frame(), height=10, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.memory_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_search_tab(self):
        search_frame = ttk.Frame(self.notebook)
        self.notebook.add(search_frame, text="Search")
        
        # Advanced Search Engine Integration
        try:
            from advanced_search_engine import search_engine
            self.advanced_search_available = True
        except ImportError:
            self.advanced_search_available = False
            print("Warning: Advanced search engine not available")
        
        # Search type selection
        search_type_frame = CanvasLabelFrame(search_frame, text="Search Type", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        search_type_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.search_type = tk.StringVar(value="basic")
        ttk.Radiobutton(search_type_frame, text="Basic Search", variable=self.search_type, value="basic").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(search_type_frame, text="Combi_Fetch (Multi-Engine)", variable=self.search_type, value="combi").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(search_type_frame, text="Folder_Fetch (Local Files)", variable=self.search_type, value="folder").pack(side=tk.LEFT, padx=(0, 10))
        
        # Basic search interface
        basic_frame = CanvasLabelFrame(search_frame, text="Basic Search", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        query_frame = ttk.Frame(basic_frame)
        query_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(query_frame, text="Query:").pack(side=tk.LEFT)
        self.search_query = tk.StringVar()
        ttk.Entry(query_frame, textvariable=self.search_query, width=40).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(query_frame, text="Search", command=self.execute_search).pack(side=tk.LEFT, padx=(5, 0))
        
        # Search options
        options_frame = ttk.Frame(basic_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(options_frame, text="Scope:").pack(side=tk.LEFT)
        self.search_scope = tk.StringVar(value="both")
        scope_combo = ttk.Combobox(options_frame, textvariable=self.search_scope, values=["both", "web_only", "docs_only"], state="readonly", width=10)
        scope_combo.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(options_frame, text="Focus:").pack(side=tk.LEFT)
        self.search_focus = tk.StringVar(value="general")
        focus_combo = ttk.Combobox(options_frame, textvariable=self.search_focus, values=["technical", "tutorials", "downloads", "documentation", "general"], state="readonly", width=10)
        focus_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Combi_Fetch interface
        combi_frame = CanvasLabelFrame(search_frame, text="Combi_Fetch - Multi-Engine Search", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        combi_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Engine selection
        engines_frame = ttk.Frame(combi_frame)
        engines_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(engines_frame, text="Engines:").pack(side=tk.LEFT)
        
        self.selected_engines = {
            'brave': tk.BooleanVar(value=True),
            'gemini': tk.BooleanVar(value=True),
            'github': tk.BooleanVar(value=True),
            'wikipedia': tk.BooleanVar(value=True),
            'arxiv': tk.BooleanVar(value=True),
            'stackoverflow': tk.BooleanVar(value=True),
            'reddit': tk.BooleanVar(value=False),
            'hackernews': tk.BooleanVar(value=False)
        }
        
        engine_buttons_frame = tk.Frame(engines_frame, bg=self.bg_dark)
        engine_buttons_frame.pack(side=tk.LEFT, padx=(5, 0))
        
        row_frame = None
        col = 0
        for i, (engine, var) in enumerate(self.selected_engines.items()):
            if col == 0:
                row_frame = tk.Frame(engine_buttons_frame, bg=self.bg_dark)
                row_frame.pack(fill=tk.X)
            ttk.Checkbutton(row_frame, text=engine.title(), variable=var).pack(side=tk.LEFT, padx=(0, 10))
            col += 1
            if col > 3:
                col = 0
        
        # Combi_Fetch controls
        combi_controls_frame = ttk.Frame(combi_frame)
        combi_controls_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(combi_controls_frame, text="Max Results:").pack(side=tk.LEFT)
        self.combi_max_results = tk.IntVar(value=10)
        ttk.Spinbox(combi_controls_frame, from_=1, to=50, textvariable=self.combi_max_results, width=5).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(combi_controls_frame, text="Combi_Fetch", command=self.execute_combi_fetch).pack(side=tk.LEFT, padx=(10, 0))
        
        # Folder_Fetch interface
        folder_frame = CanvasLabelFrame(search_frame, text="Folder_Fetch - Local File Search", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Folder selection
        folder_select_frame = ttk.Frame(folder_frame)
        folder_select_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(folder_select_frame, text="Folder:").pack(side=tk.LEFT)
        self.folder_path = tk.StringVar(value=os.getcwd())
        ttk.Entry(folder_select_frame, textvariable=self.folder_path, width=40).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(folder_select_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT, padx=(5, 0))
        
        # Folder_Fetch options
        folder_options_frame = ttk.Frame(folder_frame)
        folder_options_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_options_frame, text="Mode:").pack(side=tk.LEFT)
        self.folder_mode = tk.StringVar(value="swift")
        mode_combo = ttk.Combobox(folder_options_frame, textvariable=self.folder_mode, values=["swift", "deep"], state="readonly", width=8)
        mode_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        ttk.Label(folder_options_frame, text="File Types:").pack(side=tk.LEFT)
        self.file_types = tk.StringVar(value=".py,.md,.txt,.js,.html,.css,.json")
        ttk.Entry(folder_options_frame, textvariable=self.file_types, width=20).pack(side=tk.LEFT, padx=(5, 10))
        
        self.recursive_search = tk.BooleanVar(value=True)
        ttk.Checkbutton(folder_options_frame, text="Recursive", variable=self.recursive_search).pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Button(folder_options_frame, text="Folder_Fetch", command=self.execute_folder_fetch).pack(side=tk.RIGHT, padx=(10, 0))
        
        # Search results
        results_frame = CanvasLabelFrame(search_frame, text="Search Results", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        results_frame.pack(fill=tk.BOTH, expand=True)
        self.search_results = scrolledtext.ScrolledText(results_frame.get_inner_frame(), height=15, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.search_results.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_feedback_tab(self):
        feedback_frame = ttk.Frame(self.notebook)
        self.notebook.add(feedback_frame, text="Feedback")
        # Feedback collection
        collection_frame = CanvasLabelFrame(feedback_frame, text="Feedback Collection", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        collection_frame.pack(fill=tk.X, pady=(0, 10))
        # Session ID
        session_frame = ttk.Frame(collection_frame)
        session_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(session_frame, text="Session ID:").pack(side=tk.LEFT)
        self.feedback_session_id = tk.StringVar(value=f"session_{int(time.time())}")
        ttk.Entry(session_frame, textvariable=self.feedback_session_id, width=25).pack(side=tk.LEFT, padx=(5, 10))
        # Rating
        ttk.Label(session_frame, text="Rating:").pack(side=tk.LEFT)
        self.feedback_rating = tk.IntVar(value=5)
        rating_spin = ttk.Spinbox(session_frame, from_=1, to=5, textvariable=self.feedback_rating, width=5)
        rating_spin.pack(side=tk.LEFT, padx=(5, 10))
        # Feedback input
        feedback_input_frame = CanvasLabelFrame(feedback_frame, text="Feedback Input", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        feedback_input_frame.pack(fill=tk.X, pady=(0, 10))
        self.feedback_text = scrolledtext.ScrolledText(feedback_input_frame.get_inner_frame(), height=5, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.feedback_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Feedback display
        feedback_display_frame = CanvasLabelFrame(feedback_frame, text="Feedback History", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        feedback_display_frame.pack(fill=tk.BOTH, expand=True)
        self.feedback_display = scrolledtext.ScrolledText(feedback_display_frame.get_inner_frame(), height=10, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.feedback_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        # Submit button
        ttk.Button(collection_frame, text="Submit Feedback", command=lambda: self.log_activity("Feedback submitted")).pack(pady=(10, 0))
        # Analytics
        analytics_frame = CanvasLabelFrame(feedback_frame, text="Feedback Analytics", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        analytics_frame.pack(fill=tk.BOTH, expand=True)
        self.analytics_display = scrolledtext.ScrolledText(analytics_frame.get_inner_frame(), height=10, bg=self.bg_dark, fg=self.fg_light, insertbackground=self.accent, font=('Fira Mono', 11))
        self.analytics_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_heartbeat_tab(self):
        heartbeat_frame = ttk.Frame(self.notebook)
        self.notebook.add(heartbeat_frame, text="Heartbeat")
        # Heartbeat controls
        controls_frame = CanvasLabelFrame(heartbeat_frame, text="Heartbeat Controls", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(controls_frame, text="Refresh Status", command=self.refresh_heartbeat_status).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Force Reset", command=self.force_heartbeat_reset).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Show Details", command=self.show_heartbeat_details).pack(side=tk.LEFT, padx=(0, 5))
        # Layer status grid (now using pack)
        layers_frame = CanvasLabelFrame(heartbeat_frame, text="Layer Status", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        layers_frame.pack(fill=tk.X, pady=(0, 10))
        self.layer_status_labels = {}
        for layer_name in ['ui', 'connection', 'memory', 'mcp', 'monitoring', 'ai_agent']:
            row_frame = tk.Frame(layers_frame.get_inner_frame(), bg=self.bg_dark)
            row_frame.pack(fill=tk.X, pady=2)
            ttk.Label(row_frame, text=f"{layer_name.upper()}:").pack(side=tk.LEFT, padx=(0, 10))
            status_label = ttk.Label(row_frame, text="Detecting...", style='Status.TLabel')
            status_label.pack(side=tk.LEFT)
            self.layer_status_labels[layer_name] = status_label
        # Heartbeat status display
        heartbeat_display_frame = CanvasLabelFrame(heartbeat_frame, text="Heartbeat Status", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        heartbeat_display_frame.pack(fill=tk.BOTH, expand=True)
        self.heartbeat_display = scrolledtext.ScrolledText(heartbeat_display_frame.get_inner_frame(), height=15, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.heartbeat_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_ai_agent_tab(self):
        ai_agent_frame = ttk.Frame(self.notebook)
        self.notebook.add(ai_agent_frame, text="AI Agent")
        # Agent controls
        controls_frame = CanvasLabelFrame(ai_agent_frame, text="AI Agent Controls", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(controls_frame, text="Load Context", command=self.load_agent_context).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Save Memory", command=self.save_agent_memory).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Show Patterns", command=self.show_learning_patterns).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Auto-Respond", command=self.toggle_auto_response).pack(side=tk.LEFT, padx=(0, 5))
        # Agent status
        status_frame = CanvasLabelFrame(ai_agent_frame, text="Agent Status", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        self.agent_status_text = tk.StringVar(value="Agent Status: Active and Learning")
        ttk.Label(status_frame, textvariable=self.agent_status_text, style='Status.TLabel').pack(anchor=tk.W)
        # Agent memory display
        memory_display_frame = CanvasLabelFrame(ai_agent_frame, text="Agent Memory", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        memory_display_frame.pack(fill=tk.BOTH, expand=True)
        self.agent_memory_display = scrolledtext.ScrolledText(memory_display_frame.get_inner_frame(), height=15, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.agent_memory_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        # Initialize agent memory display
        self.update_agent_memory_display()

    def setup_conversation_tab(self):
        """Setup conversation continuity tab"""
        conversation_frame = ttk.Frame(self.notebook)
        self.notebook.add(conversation_frame, text="Conversation")
        
        # Initialize context-aware agent
        try:
            from context_aware_agent import context_agent
            self.context_agent = context_agent
            self.context_agent_available = True
        except ImportError:
            self.context_agent_available = False
            print("Warning: Context-aware agent not available")
        
        # Conversation controls
        controls_frame = CanvasLabelFrame(conversation_frame, text="Conversation Controls", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Toggle buttons
        toggle_frame = ttk.Frame(controls_frame)
        toggle_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.conversation_continuity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(toggle_frame, text="Conversation Continuity", 
                       variable=self.conversation_continuity_var,
                       command=self.toggle_conversation_continuity).pack(side=tk.LEFT, padx=(0, 10))
        
        self.auto_response_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(toggle_frame, text="Auto Response", 
                       variable=self.auto_response_var,
                       command=self.toggle_auto_response_conversation).pack(side=tk.LEFT, padx=(0, 10))
        
        # Response delay
        delay_frame = ttk.Frame(controls_frame)
        delay_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(delay_frame, text="Response Delay (seconds):").pack(side=tk.LEFT)
        self.response_delay_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(delay_frame, from_=0.0, to=5.0, increment=0.1, 
                   textvariable=self.response_delay_var, width=5,
                   command=self.set_response_delay).pack(side=tk.LEFT, padx=(5, 10))
        
        # Conversation input
        input_frame = CanvasLabelFrame(conversation_frame, text="Conversation", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Message input
        message_frame = ttk.Frame(input_frame)
        message_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(message_frame, text="Message:").pack(side=tk.LEFT)
        self.conversation_message = tk.StringVar()
        ttk.Entry(message_frame, textvariable=self.conversation_message, width=50).pack(side=tk.LEFT, padx=(5, 10))
        ttk.Button(message_frame, text="Send", command=self.send_conversation_message).pack(side=tk.LEFT, padx=(5, 0))
        
        # Conversation display
        conversation_display_frame = CanvasLabelFrame(conversation_frame, text="Conversation History", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        conversation_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.conversation_display = scrolledtext.ScrolledText(conversation_display_frame.get_inner_frame(), height=15, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.conversation_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Context information
        context_frame = CanvasLabelFrame(conversation_frame, text="Context Information", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        context_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.context_display = scrolledtext.ScrolledText(context_frame.get_inner_frame(), height=8, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.context_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Action buttons
        action_frame = ttk.Frame(conversation_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(action_frame, text="Clear History", command=self.clear_conversation_history).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Save State", command=self.save_conversation_state).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Load State", command=self.load_conversation_state).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(action_frame, text="Show Summary", command=self.show_conversation_summary).pack(side=tk.LEFT, padx=(0, 5))
        
        # Initialize conversation
        if self.context_agent_available:
            self.update_context_display()
            self.conversation_display.insert(tk.END, "Conversation system initialized. Type a message to start!\n")
        else:
            self.conversation_display.insert(tk.END, "Context-aware agent not available. Please check installation.\n")

    def setup_logs_tab(self):
        logs_frame = ttk.Frame(self.notebook)
        self.notebook.add(logs_frame, text="Logs")
        # Log controls
        controls_frame = ttk.Frame(logs_frame)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(controls_frame, text="Refresh Logs", command=self.refresh_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Save Logs", command=self.save_logs).pack(side=tk.LEFT, padx=(0, 5))
        # Logs display
        logs_display_frame = CanvasLabelFrame(logs_frame, text="System Logs", border_color=self.outline_grey, bg=self.bg_dark, fg=self.fg_light, accent=self.accent, label_green=True)
        logs_display_frame.pack(fill=tk.BOTH, expand=True)
        self.logs_display = scrolledtext.ScrolledText(logs_display_frame.get_inner_frame(), height=20, bg=self.terminal_bg, fg=self.terminal_fg, insertbackground=self.accent, font=('Fira Mono', 11))
        self.logs_display.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    def setup_llm_model_selector(self, parent):
        """Add a dropdown for selecting Ollama models."""
        models = model_validation.list_local_ollama_models()
        self.model_var = tk.StringVar(value=models[0] if models else "")
        model_label = ttk.Label(parent, text="Ollama Model:", foreground=self.accent)
        model_label.pack(side=tk.LEFT, padx=(0, 8))
        model_dropdown = ttk.Combobox(parent, textvariable=self.model_var, values=models, state="readonly")
        model_dropdown.pack(side=tk.LEFT)
        status_label = ttk.Label(parent, text="", foreground=self.accent)
        status_label.pack(side=tk.LEFT, padx=(8, 0))
        def on_model_change(event):
            selected = self.model_var.get()
            actual = llm_manager.set_ollama_model(selected)
            if actual == selected:
                status_label.config(text=f"Model set: {actual}")
            else:
                status_label.config(text=f"Auto-corrected to: {actual}")
        model_dropdown.bind("<<ComboboxSelected>>", on_model_change)

    def initialize_heartbeat_system(self):
        self.heartbeat_layers = {
            'ui': {'status': 'active', 'last_beat': time.time(), 'priority': 1},
            'connection': {'status': 'active', 'last_beat': time.time(), 'priority': 2},
            'memory': {'status': 'active', 'last_beat': time.time(), 'priority': 3},
            'mcp': {'status': 'active', 'last_beat': time.time(), 'priority': 4},
            'monitoring': {'status': 'active', 'last_beat': time.time(), 'priority': 5},
            'ai_agent': {'status': 'active', 'last_beat': time.time(), 'priority': 6, 'context_awareness': 'high', 'session_memory': True, 'learning_capability': True}
        }
        self.heartbeat_interval = 2.0
        self.heartbeat_timeout = 10.0
        self.context_chain = []
        self.agent_memory = {}
        self.agent_learning_patterns = []
        self.log_activity("Heartbeat system initialized with AI Agent layer")
        self.start_heartbeat_loop()

    def start_heartbeat_loop(self):
        def heartbeat_worker():
            while self.running:
                try:
                    self.send_heartbeat()
                    self.check_heartbeats()
                    self.update_agent_learning()
                    self.update_agent_memory_display()
                    self.update_context_chain()
                    self.broadcast_status()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    self.log_activity(f"Heartbeat error: {e}")
                    time.sleep(5)
        heartbeat_thread = threading.Thread(target=heartbeat_worker, daemon=True)
        heartbeat_thread.start()
        self.heartbeat_loop = heartbeat_thread  # Store the thread reference
        self.log_activity("Heartbeat loop started")

    def send_heartbeat(self):
        current_time = time.time()
        self.heartbeat_layers['ui']['last_beat'] = current_time
        self.heartbeat_layers['ui']['status'] = 'active'
        self.heartbeat_to_connection()
        self.heartbeat_to_memory()
        self.heartbeat_to_mcp()
        self.heartbeat_to_monitoring()
        self.heartbeat_to_ai_agent()

    def heartbeat_to_connection(self):
        try:
            self.heartbeat_layers['connection']['last_beat'] = time.time()
            self.heartbeat_layers['connection']['status'] = 'active'
            self.heartbeat_layers['connection']['health'] = 'good'
        except Exception as e:
            self.heartbeat_layers['connection']['status'] = 'error'
            self.heartbeat_layers['connection']['error'] = str(e)

    def heartbeat_to_memory(self):
        try:
            self.heartbeat_layers['memory']['last_beat'] = time.time()
            self.heartbeat_layers['memory']['status'] = 'active'
            self.heartbeat_layers['memory']['health'] = 'good'
        except Exception as e:
            self.heartbeat_layers['memory']['status'] = 'error'
            self.heartbeat_layers['memory']['error'] = str(e)

    def heartbeat_to_mcp(self):
        try:
            self.heartbeat_layers['mcp']['last_beat'] = time.time()
            self.heartbeat_layers['mcp']['status'] = 'active'
            self.heartbeat_layers['mcp']['health'] = 'good'
        except Exception as e:
            self.heartbeat_layers['mcp']['status'] = 'error'
            self.heartbeat_layers['mcp']['error'] = str(e)

    def heartbeat_to_monitoring(self):
        try:
            self.heartbeat_layers['monitoring']['last_beat'] = time.time()
            self.heartbeat_layers['monitoring']['status'] = 'active'
            self.heartbeat_layers['monitoring']['health'] = 'good'
        except Exception as e:
            self.heartbeat_layers['monitoring']['status'] = 'error'
            self.heartbeat_layers['monitoring']['error'] = str(e)

    def heartbeat_to_ai_agent(self):
        try:
            # AI Agent self-monitoring
            self.heartbeat_layers['ai_agent']['last_beat'] = time.time()
            self.heartbeat_layers['ai_agent']['status'] = 'active'
            self.heartbeat_layers['ai_agent']['health'] = 'good'
            self.heartbeat_layers['ai_agent']['context_awareness'] = 'high'
            self.heartbeat_layers['ai_agent']['session_memory'] = True
            self.heartbeat_layers['ai_agent']['learning_capability'] = True
            # Update agent memory with current state
            self.agent_memory['last_heartbeat'] = time.time()
            self.agent_memory['active_session'] = True
            self.agent_memory['context_chain_length'] = len(self.context_chain)
        except Exception as e:
            self.heartbeat_layers['ai_agent']['status'] = 'error'
            self.heartbeat_layers['ai_agent']['error'] = str(e)

    def check_heartbeats(self):
        current_time = time.time()
        for layer_name, layer_info in self.heartbeat_layers.items():
            time_since_beat = current_time - layer_info['last_beat']
            if time_since_beat > self.heartbeat_timeout:
                layer_info['status'] = 'timeout'
                self.log_activity(f"Heartbeat timeout detected for {layer_name}")
                # Trigger AI Agent intelligent response
                self.agent_intelligent_response('heartbeat_timeout', {'layer': layer_name, 'timeout': time_since_beat})
            else:
                layer_info['status'] = 'active'
            # Update UI
            if layer_name in self.layer_status_labels:
                status_text = f"{layer_info['status'].upper()}"
                if layer_info['status'] == 'active':
                    self.layer_status_labels[layer_name].config(text=status_text, foreground='green')
                else:
                    self.layer_status_labels[layer_name].config(text=status_text, foreground='red')

    def update_context_chain(self):
        try:
            current_time = time.time()
            context_entry = {
                'timestamp': current_time,
                'layers': {name: info['status'] for name, info in self.heartbeat_layers.items()},
                'agent_memory': len(self.agent_memory),
                'learning_patterns': len(self.agent_learning_patterns),
                'auto_response_enabled': getattr(self, 'auto_response_enabled', False)
            }
            self.context_chain.append(context_entry)
            # Keep only last 100 entries
            if len(self.context_chain) > 100:
                self.context_chain = self.context_chain[-100:]
            # Update agent memory with context chain info
            self.agent_memory['context_chain_length'] = len(self.context_chain)
            self.agent_memory['last_context_update'] = current_time
        except Exception as e:
            self.log_activity(f"Context chain update error: {e}")

    def broadcast_status(self):
        try:
            status_data = {
                'timestamp': time.time(),
                'layers': {name: info['status'] for name, info in self.heartbeat_layers.items()},
                'agent_status': {
                    'active': True,
                    'memory_size': len(self.agent_memory),
                    'learning_patterns': len(self.agent_learning_patterns),
                    'auto_response': getattr(self, 'auto_response_enabled', False),
                    'context_awareness': 'high'
                }
            }
            # Save status to file
            with open('heartbeat_status.json', 'w') as f:
                json.dump(status_data, f, indent=2)
            self.log_activity("Status broadcasted with AI Agent integration")
        except Exception as e:
            self.log_activity(f"Status broadcast error: {e}")

    def refresh_heartbeat_status(self):
        self.update_heartbeat_display()
        self.log_activity("Heartbeat status refreshed")

    def update_heartbeat_display(self):
        try:
            for layer_name, label in self.layer_status_labels.items():
                if layer_name in self.heartbeat_layers:
                    layer_info = self.heartbeat_layers[layer_name]
                    status = layer_info['status']
                    if status == 'active':
                        label.config(text="Active")
                    elif status == 'warning':
                        label.config(text="Warning")
                    elif status == 'timeout':
                        label.config(text="Timeout")
                    elif status == 'error':
                        label.config(text="Error")
                    else:
                        label.config(text="Unknown")
            status_text = "HEARTBEAT SYSTEM STATUS\n"
            status_text += "=" * 50 + "\n\n"
            for layer_name, layer_info in self.heartbeat_layers.items():
                time_since_beat = time.time() - layer_info['last_beat']
                status_text += f"Layer: {layer_name.upper()}\n"
                status_text += f"  Status: {layer_info['status']}\n"
                status_text += f"  Last Beat: {time_since_beat:.1f}s ago\n"
                status_text += f"  Health: {layer_info.get('health', 'unknown')}\n\n"
            status_text += f"Context Chain Length: {len(self.context_chain)}\n"
            status_text += f"Last Update: {datetime.now().strftime('%H:%M:%S')}\n"
            self.heartbeat_display.delete('1.0', tk.END)
            self.heartbeat_display.insert('1.0', status_text)
        except Exception as e:
            self.heartbeat_display.delete('1.0', tk.END)
            self.heartbeat_display.insert('1.0', f"Heartbeat display error: {e}")

    def show_heartbeat_details(self):
        try:
            details = {
                'layers': self.heartbeat_layers.copy(),
                'context_chain_length': len(self.context_chain),
                'last_context': self.context_chain[-1] if self.context_chain else None
            }
            details_text = json.dumps(details, indent=2)
            details_window = tk.Toplevel(self.root)
            details_window.title("Heartbeat Details")
            details_window.geometry("600x400")
            text_widget = scrolledtext.ScrolledText(details_window, bg=self.bg_dark, fg=self.fg_light)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert('1.0', details_text)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show heartbeat details: {e}")

    def force_heartbeat_reset(self):
        current_time = time.time()
        for layer_name in self.heartbeat_layers:
            self.heartbeat_layers[layer_name]['last_beat'] = current_time
            self.heartbeat_layers[layer_name]['status'] = 'active'
        self.log_activity("Forced heartbeat reset - all layers marked active")

    def log_activity(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        # Update UI log
        self.activity_log.insert(tk.END, log_entry)
        self.activity_log.see(tk.END)
        # Write to persistent log file
        self.write_to_action_log(log_entry)
        if hasattr(self, 'status_bar'):
            self.status_bar.config(text=message)

    def write_to_action_log(self, log_entry):
        try:
            log_file = "agent_action_log.md"
            # Check if we need to rotate the log
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    line_count = sum(1 for _ in f)
                if line_count >= 2000:
                    self.rotate_action_log()
            # Append to current log
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to action log: {e}")

    def rotate_action_log(self):
        try:
            import glob
            # Find existing rotated logs
            existing_logs = glob.glob("agent_action_log_*.md")
            if existing_logs:
                # Get the highest number
                numbers = [int(log.split('_')[-1].split('.')[0]) for log in existing_logs]
                next_num = max(numbers) + 1
            else:
                next_num = 1
            # Rename current log
            new_name = f"agent_action_log_{next_num:03d}.md"
            os.rename("agent_action_log.md", new_name)
            # Keep only last 3 files
            if len(existing_logs) >= 3:
                oldest_log = min(existing_logs, key=os.path.getctime)
                os.remove(oldest_log)
        except Exception as e:
            print(f"Error rotating action log: {e}")

    def load_context_from_log(self):
        try:
            log_file = "agent_action_log.md"
            if not os.path.exists(log_file):
                messagebox.showinfo("Info", "No action log found.")
                return
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Show log content in a new window
            log_window = tk.Toplevel(self.root)
            log_window.title("Action Log Content")
            log_window.geometry("800x600")
            text_widget = scrolledtext.ScrolledText(log_window, bg=self.bg_dark, fg=self.fg_light)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert('1.0', content)
            self.log_activity("Action log loaded for context review.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load action log: {e}")

    def view_all_logs(self):
        try:
            import glob
            log_files = glob.glob("agent_action_log*.md")
            if not log_files:
                messagebox.showinfo("Info", "No log files found.")
                return
            # Show list of log files
            log_window = tk.Toplevel(self.root)
            log_window.title("All Log Files")
            log_window.geometry("400x300")
            listbox = tk.Listbox(log_window)
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            for log_file in sorted(log_files):
                listbox.insert(tk.END, log_file)
            self.log_activity("Log file list displayed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to list log files: {e}")

    def refresh_logs(self):
        self.log_activity("Logs refreshed")

    def clear_logs(self):
        self.logs_display.delete('1.0', tk.END)
        self.log_activity("Logs cleared")

    def save_logs(self):
        try:
            filename = filedialog.asksaveasfilename(title="Save Logs", defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.logs_display.get('1.0', tk.END))
                self.log_activity(f"Logs saved to: {filename}")
                messagebox.showinfo("Success", f"Logs saved to {filename}")
        except Exception as e:
            self.log_activity(f"Save logs error: {e}")
            messagebox.showerror("Error", f"Failed to save logs: {e}")

    def start_monitoring(self):
        def monitor():
            while self.running:
                try:
                    self.root.after(0, self.update_heartbeat_display)
                    time.sleep(5)
                except Exception as e:
                    self.log_activity(f"Monitoring error: {e}")
                    time.sleep(10)
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()

    def on_closing(self):
        self.running = False
        self.root.destroy()

    def load_agent_context(self):
        try:
            # Load context from action log
            log_file = "agent_action_log.md"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Parse recent actions for context
                lines = content.split('\n')[-50:]  # Last 50 lines
                recent_actions = [line for line in lines if line.strip() and ']' in line]
                self.agent_memory['recent_context'] = recent_actions
                self.agent_memory['context_loaded'] = time.time()
                self.log_activity("AI Agent context loaded from action log")
                self.update_agent_memory_display()
                messagebox.showinfo("Success", "Agent context loaded successfully!")
            else:
                messagebox.showinfo("Info", "No action log found to load context from.")
        except Exception as e:
            self.log_activity(f"Failed to load agent context: {e}")
            messagebox.showerror("Error", f"Failed to load agent context: {e}")

    def save_agent_memory(self):
        try:
            memory_file = "ai_agent_memory.json"
            memory_data = {
                'timestamp': time.time(),
                'agent_memory': self.agent_memory,
                'learning_patterns': self.agent_learning_patterns,
                'context_chain_length': len(self.context_chain),
                'heartbeat_layers': {name: info['status'] for name, info in self.heartbeat_layers.items()}
            }
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(memory_data, f, indent=2)
            self.log_activity("AI Agent memory saved to persistent storage")
            messagebox.showinfo("Success", "Agent memory saved successfully!")
        except Exception as e:
            self.log_activity(f"Failed to save agent memory: {e}")
            messagebox.showerror("Error", f"Failed to save agent memory: {e}")

    def update_agent_memory_display(self):
        try:
            memory_text = "AI AGENT MEMORY STATUS\n"
            memory_text += "=" * 50 + "\n\n"
            memory_text += f"Session Active: {self.agent_memory.get('active_session', False)}\n"
            memory_text += f"Last Heartbeat: {self.agent_memory.get('last_heartbeat', 'Never')}\n"
            memory_text += f"Context Chain Length: {self.agent_memory.get('context_chain_length', 0)}\n"
            memory_text += f"Context Loaded: {self.agent_memory.get('context_loaded', 'Never')}\n"
            memory_text += f"Learning Patterns: {len(self.agent_learning_patterns)}\n\n"
            memory_text += "Recent Context:\n"
            recent_context = self.agent_memory.get('recent_context', [])
            for action in recent_context[-10:]:  # Show last 10 actions
                memory_text += f"  {action}\n"
            memory_text += f"\nLast Update: {datetime.now().strftime('%H:%M:%S')}\n"
            self.agent_memory_display.delete('1.0', tk.END)
            self.agent_memory_display.insert('1.0', memory_text)
        except Exception as e:
            self.agent_memory_display.delete('1.0', tk.END)
            self.agent_memory_display.insert('1.0', f"Agent memory display error: {e}")

    def show_learning_patterns(self):
        try:
            patterns_text = "AI AGENT LEARNING PATTERNS\n"
            patterns_text += "=" * 50 + "\n\n"
            if self.agent_learning_patterns:
                for i, pattern in enumerate(self.agent_learning_patterns, 1):
                    patterns_text += f"Pattern {i}:\n"
                    patterns_text += f"  Type: {pattern.get('type', 'Unknown')}\n"
                    patterns_text += f"  Confidence: {pattern.get('confidence', 0):.2f}\n"
                    patterns_text += f"  Description: {pattern.get('description', 'No description')}\n\n"
            else:
                patterns_text += "No learning patterns detected yet.\n"
                patterns_text += "Patterns will emerge as the agent learns from interactions.\n"
            # Show in new window
            patterns_window = tk.Toplevel(self.root)
            patterns_window.title("AI Agent Learning Patterns")
            patterns_window.geometry("600x400")
            text_widget = scrolledtext.ScrolledText(patterns_window, bg=self.bg_dark, fg=self.fg_light)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            text_widget.insert('1.0', patterns_text)
            self.log_activity("AI Agent learning patterns displayed")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show learning patterns: {e}")

    def toggle_auto_response(self):
        try:
            if not hasattr(self, 'auto_response_enabled'):
                self.auto_response_enabled = False
            self.auto_response_enabled = not self.auto_response_enabled
            status = "enabled" if self.auto_response_enabled else "disabled"
            self.agent_status_text.set(f"Agent Status: Active and Learning (Auto-Response: {status})")
            self.log_activity(f"AI Agent auto-response {status}")
            messagebox.showinfo("Auto-Response", f"AI Agent auto-response {status}")
        except Exception as e:
            self.log_activity(f"Failed to toggle auto-response: {e}")
            messagebox.showerror("Error", f"Failed to toggle auto-response: {e}")

    def agent_intelligent_response(self, event_type, event_data):
        try:
            if not self.auto_response_enabled:
                return
            # Analyze event and generate intelligent response
            response = self.analyze_event_and_respond(event_type, event_data)
            if response:
                self.log_activity(f"AI Agent intelligent response: {response}")
                # Add to learning patterns
                pattern = {
                    'type': 'intelligent_response',
                    'event_type': event_type,
                    'response': response,
                    'confidence': 0.8,
                    'timestamp': time.time(),
                    'description': f"Auto-responded to {event_type} event"
                }
                self.agent_learning_patterns.append(pattern)
                # Update memory
                self.agent_memory['last_auto_response'] = time.time()
                self.agent_memory['auto_response_count'] = self.agent_memory.get('auto_response_count', 0) + 1
                self.update_agent_memory_display()
        except Exception as e:
            self.log_activity(f"AI Agent intelligent response failed: {e}")

    def analyze_event_and_respond(self, event_type, event_data):
        try:
            # Simple intelligent response system
            responses = {
                'heartbeat_timeout': "Detected heartbeat timeout. Initiating system health check and recovery procedures.",
                'memory_error': "Memory operation failed. Attempting to restore from backup and clear corrupted data.",
                'connection_lost': "Connection lost. Attempting to reconnect and restore session state.",
                'search_error': "Search operation failed. Switching to alternative search methods.",
                'feedback_received': "User feedback received. Updating learning patterns and adjusting behavior.",
                'system_startup': "System startup detected. Loading previous context and initializing agent memory.",
                'error_detected': "Error detected in system. Analyzing pattern and implementing preventive measures."
            }
            return responses.get(event_type, f"Processing {event_type} event with adaptive response.")
        except Exception as e:
            return f"Error in event analysis: {e}"

    def update_agent_learning(self):
        try:
            # Update learning patterns based on current system state
            current_time = time.time()
            # Check for new patterns
            if len(self.context_chain) > 5:
                pattern = {
                    'type': 'context_chain_growth',
                    'confidence': 0.7,
                    'timestamp': current_time,
                    'description': f"Context chain has grown to {len(self.context_chain)} items"
                }
                if pattern not in self.agent_learning_patterns:
                    self.agent_learning_patterns.append(pattern)
            # Check for system health patterns
            healthy_layers = sum(1 for layer in self.heartbeat_layers.values() if layer.get('status') == 'active')
            if healthy_layers == len(self.heartbeat_layers):
                pattern = {
                    'type': 'system_health_optimal',
                    'confidence': 0.9,
                    'timestamp': current_time,
                    'description': "All system layers are healthy and active"
                }
                if pattern not in self.agent_learning_patterns:
                    self.agent_learning_patterns.append(pattern)
            # Update agent memory
            self.agent_memory['learning_update_time'] = current_time
            self.agent_memory['total_patterns'] = len(self.agent_learning_patterns)
        except Exception as e:
            self.log_activity(f"Agent learning update failed: {e}")

    # Advanced Search Methods
    def execute_search(self):
        """Execute basic search"""
        query = self.search_query.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return
        
        self.log_activity(f"Basic search executed: {query}")
        self.search_results.delete('1.0', tk.END)
        self.search_results.insert('1.0', f"Searching for: {query}\n\n")
        self.search_results.insert(tk.END, "Basic search functionality - results would appear here\n")
        self.search_results.insert(tk.END, f"Scope: {self.search_scope.get()}\n")
        self.search_results.insert(tk.END, f"Focus: {self.search_focus.get()}\n")
    
    def execute_combi_fetch(self):
        """Execute Combi_Fetch multi-engine search"""
        query = self.search_query.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return
        
        if not self.advanced_search_available:
            messagebox.showerror("Error", "Advanced search engine not available")
            return
        
        # Get selected engines
        selected_engines = [engine for engine, var in self.selected_engines.items() if var.get()]
        if not selected_engines:
            messagebox.showwarning("Warning", "Please select at least one search engine")
            return
        
        self.log_activity(f"Combi_Fetch executed: {query} on engines: {', '.join(selected_engines)}")
        
        # Clear results
        self.search_results.delete('1.0', tk.END)
        self.search_results.insert('1.0', f"Combi_Fetch: {query}\n")
        self.search_results.insert(tk.END, f"Engines: {', '.join(selected_engines)}\n")
        self.search_results.insert(tk.END, f"Max Results: {self.combi_max_results.get()}\n")
        self.search_results.insert(tk.END, "=" * 50 + "\n\n")
        
        # Execute search in background thread
        def search_worker():
            try:
                from advanced_search_engine import search_engine
                results = search_engine.combi_fetch(
                    query=query,
                    engines=selected_engines,
                    max_results=self.combi_max_results.get()
                )
                
                # Update UI with results
                self.root.after(0, lambda: self.display_combi_results(results, query, selected_engines))
                
            except Exception as e:
                error_msg = f"Combi_Fetch error: {str(e)}"
                self.log_activity(error_msg)
                self.root.after(0, lambda: self.search_results.insert(tk.END, f"Error: {error_msg}\n"))
        
        threading.Thread(target=search_worker, daemon=True).start()
    
    def display_combi_results(self, results, query, engines):
        """Display Combi_Fetch results"""
        self.search_results.delete('1.0', tk.END)
        
        # Summary
        self.search_results.insert(tk.END, f"Combi_Fetch Results for: {query}\n")
        self.search_results.insert(tk.END, f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        self.search_results.insert(tk.END, f"Engines Used: {', '.join(engines)}\n")
        self.search_results.insert(tk.END, f"Total Results: {len(results)}\n")
        self.search_results.insert(tk.END, "=" * 50 + "\n\n")
        
        # Display results
        if results:
            self.search_results.insert(tk.END, "TOP RESULTS:\n")
            for i, result in enumerate(results[:20], 1):  # Show top 20 results
                self.search_results.insert(tk.END, f"{i}. [{result.source}] {result.title}\n")
                self.search_results.insert(tk.END, f"   URL: {result.url}\n")
                self.search_results.insert(tk.END, f"   Relevance: {result.relevance_score:.3f}\n")
                self.search_results.insert(tk.END, f"   Snippet: {result.snippet[:200]}...\n")
                self.search_results.insert(tk.END, "-" * 30 + "\n")
        else:
            self.search_results.insert(tk.END, "No results found.\n")
        
        # Store results in memory
        self.agent_memory['last_combi_fetch'] = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'total_results': len(results),
            'engines_used': engines
        }
    
    def execute_folder_fetch(self):
        """Execute Folder_Fetch local file search"""
        query = self.search_query.get()
        if not query:
            messagebox.showwarning("Warning", "Please enter a search query")
            return
        
        folder_path = self.folder_path.get()
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", f"Folder does not exist: {folder_path}")
            return
        
        if not self.advanced_search_available:
            messagebox.showerror("Error", "Advanced search engine not available")
            return
        
        self.log_activity(f"Folder_Fetch executed: {query} in {folder_path}")
        
        # Clear results
        self.search_results.delete('1.0', tk.END)
        self.search_results.insert('1.0', f"Folder_Fetch: {query}\n")
        self.search_results.insert(tk.END, f"Folder: {folder_path}\n")
        self.search_results.insert(tk.END, "=" * 50 + "\n\n")
        
        # Execute search in background thread
        def search_worker():
            try:
                from advanced_search_engine import search_engine
                results = search_engine.folder_fetch(
                    query=query,
                    folder_path=folder_path,
                    max_results=50
                )
                
                # Update UI with results
                self.root.after(0, lambda: self.display_folder_results(results, query, folder_path))
                
            except Exception as e:
                error_msg = f"Folder_Fetch error: {str(e)}"
                self.log_activity(error_msg)
                self.root.after(0, lambda: self.search_results.insert(tk.END, f"Error: {error_msg}\n"))
        
        threading.Thread(target=search_worker, daemon=True).start()
    
    def display_folder_results(self, results, query, folder_path):
        """Display Folder_Fetch results"""
        self.search_results.delete('1.0', tk.END)
        
        # Summary
        self.search_results.insert(tk.END, f"Folder_Fetch Results for: {query}\n")
        self.search_results.insert(tk.END, f"Folder: {folder_path}\n")
        self.search_results.insert(tk.END, f"Total Files Found: {len(results)}\n")
        self.search_results.insert(tk.END, "=" * 50 + "\n\n")
        
        # File results
        if results:
            self.search_results.insert(tk.END, "FILES FOUND:\n")
            for i, result in enumerate(results[:50], 1):  # Show top 50 results
                self.search_results.insert(tk.END, f"{i}. {result.title}\n")
                self.search_results.insert(tk.END, f"   Path: {result.url}\n")
                self.search_results.insert(tk.END, f"   Relevance: {result.relevance_score:.3f}\n")
                self.search_results.insert(tk.END, f"   Context: {result.snippet[:200]}...\n")
                self.search_results.insert(tk.END, "-" * 30 + "\n")
        else:
            self.search_results.insert(tk.END, "No files found matching the query.\n")
        
        # Store results in memory
        self.agent_memory['last_folder_fetch'] = {
            'query': query,
            'folder': folder_path,
            'timestamp': datetime.now().isoformat(),
            'total_files': len(results)
        }
    
    def browse_folder(self):
        """Browse for folder selection"""
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)

    def send_conversation_message(self):
        """Send a message to the conversation system"""
        message = self.conversation_message.get().strip()
        if not message:
            return
        
        if not self.context_agent_available:
            self.conversation_display.insert(tk.END, f"User: {message}\n")
            self.conversation_display.insert(tk.END, "Agent: Context-aware agent not available.\n")
            self.conversation_message.set("")
            return
        
        # Display user message
        self.conversation_display.insert(tk.END, f"User: {message}\n")
        self.conversation_display.see(tk.END)
        
        # Clear input
        self.conversation_message.set("")
        
        # Process message in background thread
        def process_message():
            try:
                result = self.context_agent.process_message(message)
                response = result['response']['content']
                
                # Update UI with response
                self.root.after(0, lambda: self.conversation_display.insert(tk.END, f"Agent: {response}\n"))
                self.root.after(0, lambda: self.conversation_display.see(tk.END))
                self.root.after(0, self.update_context_display)
                
                # Log activity
                self.log_activity(f"Conversation: User said '{message[:50]}...', Agent responded")
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                self.root.after(0, lambda: self.conversation_display.insert(tk.END, f"Error: {error_msg}\n"))
                self.log_activity(error_msg)
        
        threading.Thread(target=process_message, daemon=True).start()
    
    def toggle_conversation_continuity(self):
        """Toggle conversation continuity feature"""
        if not self.context_agent_available:
            return
        
        enabled = self.context_agent.toggle_conversation_continuity()
        self.conversation_continuity_var.set(enabled)
        self.log_activity(f"Conversation continuity {'enabled' if enabled else 'disabled'}")
    
    def toggle_auto_response_conversation(self):
        """Toggle auto-response feature for conversation"""
        if not self.context_agent_available:
            return
        
        enabled = self.context_agent.toggle_auto_response()
        self.auto_response_var.set(enabled)
        self.log_activity(f"Conversation auto-response {'enabled' if enabled else 'disabled'}")
    
    def set_response_delay(self):
        """Set response delay for conversation"""
        if not self.context_agent_available:
            return
        
        delay = self.response_delay_var.get()
        self.context_agent.set_response_delay(delay)
        self.log_activity(f"Response delay set to {delay} seconds")
    
    def update_context_display(self):
        """Update the context information display"""
        if not self.context_agent_available:
            return
        
        try:
            context = self.context_agent.get_conversation_summary()
            context_info = context['context']
            
            self.context_display.delete('1.0', tk.END)
            self.context_display.insert(tk.END, f"Conversation Summary:\n")
            self.context_display.insert(tk.END, f"  Summary: {context_info['summary']}\n")
            self.context_display.insert(tk.END, f"  Emotional State: {context_info['emotional_state']}\n")
            self.context_display.insert(tk.END, f"  Topics: {', '.join(context_info['topics'][:5])}\n")
            self.context_display.insert(tk.END, f"  Interaction Count: {context_info['interaction_count']}\n")
            self.context_display.insert(tk.END, f"  Flow Pattern: {' -> '.join(context_info['flow_pattern'])}\n")
            
            if context_info['last_interaction']:
                last_time = datetime.fromisoformat(context_info['last_interaction'])
                self.context_display.insert(tk.END, f"  Last Interaction: {last_time.strftime('%H:%M:%S')}\n")
            
            self.context_display.insert(tk.END, f"\nAgent Settings:\n")
            self.context_display.insert(tk.END, f"  Continuity: {context['conversation_continuity_enabled']}\n")
            self.context_display.insert(tk.END, f"  Auto Response: {context['auto_response_enabled']}\n")
            
        except Exception as e:
            self.context_display.delete('1.0', tk.END)
            self.context_display.insert(tk.END, f"Error updating context: {str(e)}")
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        if not self.context_agent_available:
            return
        
        self.context_agent.context.clear_history()
        self.conversation_display.delete('1.0', tk.END)
        self.conversation_display.insert(tk.END, "Conversation history cleared.\n")
        self.update_context_display()
        self.log_activity("Conversation history cleared")
    
    def save_conversation_state(self):
        """Save conversation state to file"""
        if not self.context_agent_available:
            return
        
        try:
            filename = f"conversation_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.context_agent.save_conversation_state(filename)
            self.log_activity(f"Conversation state saved to {filename}")
            messagebox.showinfo("Success", f"Conversation state saved to {filename}")
        except Exception as e:
            error_msg = f"Error saving conversation state: {str(e)}"
            self.log_activity(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def load_conversation_state(self):
        """Load conversation state from file"""
        if not self.context_agent_available:
            return
        
        try:
            filename = filedialog.askopenfilename(
                title="Load Conversation State",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                self.context_agent.load_conversation_state(filename)
                self.update_context_display()
                self.log_activity(f"Conversation state loaded from {filename}")
                messagebox.showinfo("Success", f"Conversation state loaded from {filename}")
        except Exception as e:
            error_msg = f"Error loading conversation state: {str(e)}"
            self.log_activity(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def show_conversation_summary(self):
        """Show detailed conversation summary"""
        if not self.context_agent_available:
            return
        
        try:
            summary = self.context_agent.get_conversation_summary()
            context_info = summary['context']
            
            summary_window = tk.Toplevel(self.root)
            summary_window.title("Conversation Summary")
            summary_window.geometry("600x500")
            summary_window.configure(bg=self.bg_dark)
            
            summary_text = scrolledtext.ScrolledText(summary_window, bg=self.fg_light, fg=self.bg_dark)
            summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            summary_text.insert(tk.END, "=== CONVERSATION SUMMARY ===\n\n")
            summary_text.insert(tk.END, f"Agent ID: {summary['agent_id']}\n")
            summary_text.insert(tk.END, f"Total Interactions: {context_info['interaction_count']}\n")
            summary_text.insert(tk.END, f"Emotional State: {context_info['emotional_state']}\n")
            summary_text.insert(tk.END, f"Active Topics: {', '.join(context_info['topics'])}\n\n")
            
            summary_text.insert(tk.END, "=== RECENT MESSAGES ===\n")
            for message in context_info['recent_messages']:
                role = message['role']
                content = message['content'][:100] + "..." if len(message['content']) > 100 else message['content']
                timestamp = message['timestamp']
                summary_text.insert(tk.END, f"[{timestamp}] {role}: {content}\n")
            
            summary_text.insert(tk.END, "\n=== AGENT SETTINGS ===\n")
            summary_text.insert(tk.END, f"Conversation Continuity: {summary['conversation_continuity_enabled']}\n")
            summary_text.insert(tk.END, f"Auto Response: {summary['auto_response_enabled']}\n")
            
            self.log_activity("Conversation summary displayed")
            
        except Exception as e:
            error_msg = f"Error showing conversation summary: {str(e)}"
            self.log_activity(error_msg)
            messagebox.showerror("Error", error_msg)

def main():
    root = tk.Tk()
    app = UnifiedAgentUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main() 