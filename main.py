#!/usr/bin/env python3
"""
Beautiful Visual Drag-and-Drop Workflow Builder
Main entry point for the application.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.app import WorkflowBuilderApp

def main():
    """Main entry point for the application."""
    try:
        app = WorkflowBuilderApp()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
