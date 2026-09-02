"""Test bootstrap: run offline (echo provider) in an isolated workspace."""

import os
import sys
import tempfile
from pathlib import Path

# Ensure `import app...` works when running pytest from the backend dir.
sys.path.insert(0, str(Path(__file__).parent))

os.environ.setdefault("LLM_PROVIDER", "echo")
os.environ.setdefault("GROQ_API_KEY", "")
os.environ.setdefault("TOOL_WORKSPACE", tempfile.mkdtemp(prefix="orch_ws_"))
os.environ.setdefault("MEMORY_DIR", tempfile.mkdtemp(prefix="orch_mem_"))
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="orch_data_"))
