#!/usr/bin/env python3
"""
NexaDB Interactive CLI

Usage:
    nexadb-cli -u root -p
    nexadb-cli --host localhost --port 6970 -u root -p
    nexadb-cli --help

Interactive Commands:
    USE <collection>                  - Switch to a collection
    CREATE <json>                     - Create a document
    QUERY <json>                      - Query documents
    UPDATE <id> <json>                - Update a document
    DELETE <id>                       - Delete a document
    VECTOR_SEARCH <vector> [limit]    - Vector similarity search
    COUNT [json]                      - Count documents
    COLLECTIONS                       - List all collections
    HELP                              - Show help
    EXIT / QUIT / \\q                  - Exit CLI
"""

import sys
import argparse
import getpass
import json
import cmd
import os
from typing import Optional, Dict, Any, List

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored(text: str, color: str) -> str:
    """Return colored text for terminal output."""
    return f"{color}{text}{Colors.ENDC}"

def print_json(data: Any, indent: int = 2) -> None:
    """Pretty print JSON data with colors."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=False)
    print(colored(json_str, Colors.OKCYAN))

def print_success(message: str) -> None:
    """Print success message in green."""
    print(colored(f"✓ {message}", Colors.OKGREEN))

def print_error(message: str) -> None:
    """Print error message in red."""
    print(colored(f"✗ {message}", Colors.FAIL))

def print_info(message: str) -> None:
    """Print info message in blue."""
    print(colored(message, Colors.OKBLUE))

def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    print(colored(f"⚠ {message}", Colors.WARNING))


class NexaDBShell(cmd.Cmd):
    """Interactive NexaDB shell."""

    intro = colored(f"""
╔═══════════════════════════════════════════════════════════════════════╗
║     ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗               ║
║     ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗              ║
║     ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝              ║
║     ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗              ║
║     ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝              ║
║     ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝               ║
║                                                                       ║
║            Database for AI Developers - v2.0.0                       ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝

Type 'HELP' for commands or 'EXIT' to quit.
    """, Colors.OKCYAN)

    prompt = colored('nexadb> ', Colors.BOLD + Colors.OKGREEN)

    def __init__(self, host: str, port: int, username: str, password: str):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.current_collection: Optional[str] = None
        self.connected = False

    def preloop(self):
        """Connect to NexaDB before starting the loop."""
        try:
            # Import here to avoid issues if module not found
            from nexadb_client import NexaClient

            print_info(f"Connecting to {self.host}:{self.port}...")
            self.client = NexaClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password
            )
            self.client.connect()
            self.connected = True
            print_success(f"Connected to NexaDB v2.0.0")
            print()
        except Exception as e:
            print_error(f"Connection failed: {e}")
            print_info("Make sure NexaDB server is running:")
            print_info("  $ nexadb start")
            print()
            sys.exit(1)

    def postloop(self):
        """Disconnect when exiting."""
        if self.client and self.connected:
            self.client.disconnect()
            print_success("Disconnected from NexaDB")

    def do_USE(self, collection: str):
        """Switch to a collection.

        Usage: USE <collection>
        Example: USE movies
        """
        if not collection:
            print_error("Collection name required")
            print_info("Usage: USE <collection>")
            return

        self.current_collection = collection.strip()
        self.prompt = colored(f'nexadb({self.current_collection})> ', Colors.BOLD + Colors.OKGREEN)
        print_success(f"Switched to collection '{self.current_collection}'")

    def do_CREATE(self, args: str):
        """Create a document in the current collection.

        Usage: CREATE <json>
        Example: CREATE {"title": "The Matrix", "year": 1999}
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        if not args:
            print_error("JSON data required")
            print_info("Usage: CREATE {\"key\": \"value\"}")
            return

        try:
            data = json.loads(args)
            result = self.client.create(self.current_collection, data)
            print_success(f"Document created: {result.get('document_id', 'N/A')}")
            print_json(result)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {e}")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_QUERY(self, args: str):
        """Query documents in the current collection.

        Usage: QUERY <json>
        Example: QUERY {"year": {"$gte": 2000}}
        Example: QUERY {}  (get all documents)
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        try:
            filters = json.loads(args) if args.strip() else {}
            results = self.client.query(self.current_collection, filters, limit=100)

            if not results:
                print_warning("No documents found")
                return

            print_success(f"Found {len(results)} document(s):")
            for i, doc in enumerate(results, 1):
                print(colored(f"\n[{i}]", Colors.BOLD))
                print_json(doc)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {e}")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_UPDATE(self, args: str):
        """Update a document.

        Usage: UPDATE <id> <json>
        Example: UPDATE doc_abc123 {"age": 30}
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            print_error("Document ID and JSON data required")
            print_info("Usage: UPDATE <id> {\"key\": \"value\"}")
            return

        doc_id, json_str = parts
        try:
            updates = json.loads(json_str)
            result = self.client.update(self.current_collection, doc_id.strip(), updates)
            print_success(f"Document updated: {doc_id}")
            print_json(result)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {e}")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_DELETE(self, doc_id: str):
        """Delete a document.

        Usage: DELETE <id>
        Example: DELETE doc_abc123
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        if not doc_id:
            print_error("Document ID required")
            print_info("Usage: DELETE <id>")
            return

        try:
            result = self.client.delete(self.current_collection, doc_id.strip())
            print_success(f"Document deleted: {doc_id}")
            print_json(result)
        except Exception as e:
            print_error(f"Error: {e}")

    def do_VECTOR_SEARCH(self, args: str):
        """Vector similarity search.

        Usage: VECTOR_SEARCH <vector> [limit] [dimensions]
        Example: VECTOR_SEARCH [0.1, 0.95, 0.1, 0.8] 3 4
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        if not args:
            print_error("Vector required")
            print_info("Usage: VECTOR_SEARCH [0.1, 0.2, 0.3] [limit] [dimensions]")
            return

        try:
            # Parse vector and optional limit/dimensions
            parts = args.strip().split(']', 1)
            vector_str = parts[0] + ']'
            vector = json.loads(vector_str)

            limit = 10
            dimensions = len(vector)

            if len(parts) > 1:
                extra_args = parts[1].strip().split()
                if len(extra_args) >= 1:
                    limit = int(extra_args[0])
                if len(extra_args) >= 2:
                    dimensions = int(extra_args[1])

            results = self.client.vector_search(
                collection=self.current_collection,
                vector=vector,
                limit=limit,
                dimensions=dimensions
            )

            if not results:
                print_warning("No similar documents found")
                return

            print_success(f"Found {len(results)} similar document(s):")
            for i, result in enumerate(results, 1):
                similarity = result.get('similarity', 0) * 100
                print(colored(f"\n[{i}] {similarity:.2f}% match", Colors.BOLD))
                print_json(result['document'])
        except json.JSONDecodeError as e:
            print_error(f"Invalid vector format: {e}")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_COUNT(self, args: str):
        """Count documents in the current collection.

        Usage: COUNT [json]
        Example: COUNT {"status": "active"}
        Example: COUNT  (count all)
        """
        if not self.current_collection:
            print_error("No collection selected. Use 'USE <collection>' first.")
            return

        try:
            filters = json.loads(args) if args.strip() else {}
            results = self.client.query(self.current_collection, filters, limit=1000000)
            count = len(results)
            print_success(f"Count: {count} document(s)")
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON: {e}")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_COLLECTIONS(self, args: str):
        """List all collections.

        Usage: COLLECTIONS
        """
        try:
            # Try to list collections (if method exists)
            # For now, just show current collection
            if self.current_collection:
                print_info(f"Current collection: {self.current_collection}")
            else:
                print_warning("No collection selected")
                print_info("Use 'USE <collection>' to switch to a collection")
        except Exception as e:
            print_error(f"Error: {e}")

    def do_HELP(self, args: str):
        """Show available commands."""
        help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                        NexaDB CLI Commands                        ║
╚═══════════════════════════════════════════════════════════════════╝

Collection Management:
  USE <collection>              Switch to a collection
  COLLECTIONS                   List all collections

Document Operations:
  CREATE <json>                 Create a document
  QUERY <json>                  Query documents
  UPDATE <id> <json>            Update a document
  DELETE <id>                   Delete a document
  COUNT [json]                  Count documents

Vector Search:
  VECTOR_SEARCH <vector> [limit] [dimensions]
                                Search by vector similarity

Examples:
  USE movies
  CREATE {"title": "The Matrix", "year": 1999}
  QUERY {"year": {"$gte": 2000}}
  UPDATE doc_abc123 {"year": 2000}
  DELETE doc_abc123
  VECTOR_SEARCH [0.1, 0.95, 0.1, 0.8] 3 4
  COUNT {"status": "active"}

System:
  HELP                          Show this help
  EXIT / QUIT / \\q              Exit CLI

Press Ctrl+C to cancel current command
Press Ctrl+D or type EXIT to quit
        """
        print(colored(help_text, Colors.OKCYAN))

    def do_EXIT(self, args: str):
        """Exit the CLI."""
        print_info("Goodbye! 👋")
        return True

    def do_QUIT(self, args: str):
        """Exit the CLI."""
        return self.do_EXIT(args)

    def do_EOF(self, args: str):
        """Handle Ctrl+D."""
        print()  # New line
        return self.do_EXIT(args)

    def emptyline(self):
        """Do nothing on empty line."""
        pass

    def default(self, line: str):
        """Handle unknown commands."""
        if line.strip() == r'\q':
            return self.do_EXIT('')
        print_error(f"Unknown command: {line}")
        print_info("Type 'HELP' to see available commands")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='NexaDB Interactive CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nexadb-cli -u root -p
  nexadb-cli --host localhost --port 6970 -u admin -p
  nexadb-cli --help

Interactive Commands:
  USE movies
  CREATE {"title": "The Matrix", "year": 1999}
  QUERY {"year": {"$gte": 2000}}
  VECTOR_SEARCH [0.1, 0.95, 0.1, 0.8] 3 4
        """
    )

    parser.add_argument(
        '--host',
        default='localhost',
        help='NexaDB server host (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=6970,
        help='NexaDB server port (default: 6970)'
    )
    parser.add_argument(
        '-u', '--username',
        default='root',
        help='Username (default: root)'
    )
    parser.add_argument(
        '-p', '--password',
        action='store_true',
        help='Prompt for password'
    )
    parser.add_argument(
        '--password-stdin',
        metavar='PASSWORD',
        help='Password (not recommended, use -p instead)'
    )

    args = parser.parse_args()

    # Get password
    if args.password:
        password = getpass.getpass('Password: ')
    elif args.password_stdin:
        password = args.password_stdin
    else:
        password = 'nexadb123'  # Default password

    # Start interactive shell
    try:
        shell = NexaDBShell(
            host=args.host,
            port=args.port,
            username=args.username,
            password=password
        )
        shell.cmdloop()
    except KeyboardInterrupt:
        print()
        print_info("Goodbye! 👋")
        sys.exit(0)


if __name__ == '__main__':
    main()
