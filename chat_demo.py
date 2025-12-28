"""Web-based chat interface demo for Tata.

Run with: uv run python chat_demo.py

This starts the web server on http://localhost:8080 where you can
interact with Tata through a browser-based chat interface.
"""

import argparse
import sys

from src.tata.web.server import ChatServer, PortInUseError


def main():
    """Start the Tata chat web server."""
    parser = argparse.ArgumentParser(
        description="Start the Tata web chat interface"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to run the server on (default: 8080)"
    )
    args = parser.parse_args()
    
    print("🚀 Starting Tata Web Chat Interface")
    print("=" * 50)
    
    try:
        server = ChatServer(port=args.port)
        print(f"\n✅ Server starting on http://localhost:{args.port}")
        print("\nOpen your browser and navigate to the URL above.")
        print("Press Ctrl+C to stop the server.\n")
        print("-" * 50)
        server.run()
    except PortInUseError as e:
        print(f"\n❌ {e}")
        print(f"\nTry using a different port: uv run python chat_demo.py --port 8081")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
