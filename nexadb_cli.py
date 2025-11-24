#!/usr/bin/env python3
"""
NexaDB CLI - Interactive Terminal Client
=========================================

Interactive command-line interface for NexaDB (like MongoDB shell, Redis CLI)

Usage:
    python3 nexadb_cli.py
    python3 nexadb_cli.py --host localhost --port 6969 --api-key your_key

Commands:
    show dbs                    - List all collections
    use <collection>            - Switch to collection
    db.insert({...})           - Insert document
    db.find({...})             - Find documents
    db.update(id, {...})       - Update document
    db.delete(id)              - Delete document
    db.aggregate([...])        - Aggregation pipeline
    db.count()                 - Count documents
    db.stats()                 - Collection stats
    help                       - Show help
    exit                       - Exit CLI
"""

import sys
import json
import readline
import atexit
import os
from typing import Any, Dict, List, Optional
from nexadb_client import NexaDB, NexaDBException

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class NexaDBCLI:
    """Interactive NexaDB CLI"""

    def __init__(self, host: str = 'localhost', port: int = 6969, api_key: str = ''):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.db = None
        self.current_collection = None
        self.history_file = os.path.expanduser('~/.nexadb_history')

        # Setup readline history
        self._setup_history()

    def _setup_history(self):
        """Setup command history"""
        try:
            readline.read_history_file(self.history_file)
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        atexit.register(readline.write_history_file, self.history_file)

    def connect(self):
        """Connect to NexaDB server"""
        try:
            self.db = NexaDB(host=self.host, port=self.port, api_key=self.api_key)

            # Test connection
            status = self.db.status()

            self._print_success(f"Connected to {status['database']} v{status['version']}")
            self._print_info(f"Server: {self.host}:{self.port}")
            return True

        except Exception as e:
            self._print_error(f"Connection failed: {e}")
            self._print_info("Make sure NexaDB server is running:")
            self._print_info("  python3 nexadb_server.py")
            return False

    def _print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓{Colors.ENDC} {message}")

    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}✗{Colors.ENDC} {message}")

    def _print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.CYAN}ℹ{Colors.ENDC} {message}")

    def _print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠{Colors.ENDC} {message}")

    def _print_json(self, data: Any):
        """Pretty print JSON"""
        print(json.dumps(data, indent=2, default=str))

    def _get_prompt(self) -> str:
        """Get CLI prompt"""
        if self.current_collection:
            return f"{Colors.GREEN}nexadb:{self.current_collection}>{Colors.ENDC} "
        return f"{Colors.BLUE}nexadb>{Colors.ENDC} "

    def show_banner(self):
        """Show welcome banner"""
        banner = f"""
{Colors.BOLD}{Colors.CYAN}
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███╗   ██╗███████╗██╗  ██╗ █████╗ ██████╗ ██████╗     ║
║   ████╗  ██║██╔════╝╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗    ║
║   ██╔██╗ ██║█████╗   ╚███╔╝ ███████║██║  ██║██████╔╝    ║
║   ██║╚██╗██║██╔══╝   ██╔██╗ ██╔══██║██║  ██║██╔══██╗    ║
║   ██║ ╚████║███████╗██╔╝ ██╗██║  ██║██████╔╝██████╔╝    ║
║   ╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝     ║
║                                                           ║
║          Next-Generation Lightweight Database             ║
║                  Interactive CLI v1.0                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
{Colors.ENDC}
Type {Colors.BOLD}help{Colors.ENDC} for available commands
Type {Colors.BOLD}exit{Colors.ENDC} to quit
"""
        print(banner)

    def show_help(self):
        """Show help message"""
        help_text = f"""
{Colors.BOLD}NexaDB CLI Commands:{Colors.ENDC}

{Colors.CYAN}Connection & Navigation:{Colors.ENDC}
  show dbs                       List all collections
  use <collection>               Switch to collection
  db                             Show current collection

{Colors.CYAN}Document Operations:{Colors.ENDC}
  db.insert({{'key': 'value'}})    Insert document
  db.find({{}})                    Find all documents
  db.find({{'age': 25}})           Find with exact match
  db.find({{'age': {{'$gt': 25}}}})  Find with operators
  db.findOne({{'email': 'alice@example.com'}})
  db.findById('doc_id')          Find by ID
  db.count()                     Count documents

{Colors.CYAN}Update & Delete:{Colors.ENDC}
  db.update('id', {{'age': 30}})   Update document
  db.delete('id')                Delete document

{Colors.CYAN}Advanced Queries:{Colors.ENDC}
  db.aggregate([
    {{'$match': {{'age': {{'$gt': 25}}}}}},
    {{'$group': {{'_id': '$city', 'count': {{'$sum': 1}}}}}},
    {{'$sort': {{'count': -1}}}}
  ])

{Colors.CYAN}Query Operators:{Colors.ENDC}
  $eq, $ne                       Equality
  $gt, $gte, $lt, $lte          Comparison
  $in, $nin                      Array membership
  $regex                         Regex match
  $exists                        Field exists

{Colors.CYAN}System:{Colors.ENDC}
  stats                          Server statistics
  clear                          Clear screen
  help                           Show this help
  exit                           Exit CLI

{Colors.CYAN}Examples:{Colors.ENDC}
  use users
  db.insert({{'name': 'Alice', 'age': 28, 'city': 'NYC'}})
  db.find({{'age': {{'$gte': 25}}}})
  db.update('abc123', {{'age': 29}})
  db.delete('abc123')
"""
        print(help_text)

    def execute_command(self, command: str) -> bool:
        """Execute a command. Returns False to exit."""
        command = command.strip()

        if not command:
            return True

        # Exit commands
        if command.lower() in ('exit', 'quit', 'q'):
            self._print_info("Goodbye!")
            return False

        # Help
        if command.lower() == 'help':
            self.show_help()
            return True

        # Clear screen
        if command.lower() == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            return True

        # Show databases (collections)
        if command.lower() == 'show dbs':
            try:
                collections = self.db.list_collections()
                if collections:
                    self._print_success(f"Collections ({len(collections)}):")
                    for coll in collections:
                        print(f"  • {coll}")
                else:
                    self._print_info("No collections yet")
            except Exception as e:
                self._print_error(f"Error: {e}")
            return True

        # Use collection
        if command.lower().startswith('use '):
            collection_name = command[4:].strip()
            self.current_collection = collection_name
            self._print_success(f"Switched to collection: {collection_name}")
            return True

        # Show current collection
        if command.lower() == 'db':
            if self.current_collection:
                self._print_info(f"Current collection: {self.current_collection}")
            else:
                self._print_warning("No collection selected. Use: use <collection>")
            return True

        # Stats
        if command.lower() == 'stats':
            try:
                stats = self.db.stats()
                self._print_success("Database Statistics:")
                self._print_json(stats)
            except Exception as e:
                self._print_error(f"Error: {e}")
            return True

        # Collection operations
        if command.startswith('db.'):
            if not self.current_collection:
                self._print_warning("No collection selected. Use: use <collection>")
                return True

            self._execute_collection_command(command[3:])
            return True

        # Unknown command
        self._print_error(f"Unknown command: {command}")
        self._print_info("Type 'help' for available commands")
        return True

    def _execute_collection_command(self, command: str):
        """Execute collection-specific command"""
        collection = self.db.collection(self.current_collection)

        try:
            # Insert
            if command.startswith('insert('):
                data_str = command[7:-1]  # Extract content between ( )
                data = eval(data_str)
                doc_id = collection.insert(data)
                self._print_success(f"Document inserted: {doc_id}")

            # Find
            elif command.startswith('find('):
                query_str = command[5:-1]
                query = eval(query_str) if query_str else {}
                results = collection.find(query, limit=100)
                self._print_success(f"Found {len(results)} documents:")
                for doc in results:
                    self._print_json(doc)
                    print()

            # Find one
            elif command.startswith('findOne('):
                query_str = command[8:-1]
                query = eval(query_str)
                result = collection.find_one(query)
                if result:
                    self._print_success("Document found:")
                    self._print_json(result)
                else:
                    self._print_info("No document found")

            # Find by ID
            elif command.startswith('findById('):
                doc_id = command[10:-2]  # Extract ID from quotes
                result = collection.find_by_id(doc_id)
                if result:
                    self._print_success("Document found:")
                    self._print_json(result)
                else:
                    self._print_info("No document found")

            # Update
            elif command.startswith('update('):
                # Extract parameters
                params_str = command[7:-1]
                parts = params_str.split(',', 1)
                doc_id = parts[0].strip().strip("'\"")
                updates = eval(parts[1].strip())

                success = collection.update(doc_id, updates)
                if success:
                    self._print_success(f"Document updated: {doc_id}")
                else:
                    self._print_warning("Document not found")

            # Delete
            elif command.startswith('delete('):
                doc_id = command[7:-1].strip().strip("'\"")
                success = collection.delete(doc_id)
                if success:
                    self._print_success(f"Document deleted: {doc_id}")
                else:
                    self._print_warning("Document not found")

            # Count
            elif command.startswith('count()'):
                count = collection.count()
                self._print_success(f"Total documents: {count}")

            # Aggregate
            elif command.startswith('aggregate('):
                pipeline_str = command[10:-1]
                pipeline = eval(pipeline_str)
                results = collection.aggregate(pipeline)
                self._print_success(f"Aggregation results ({len(results)} documents):")
                self._print_json(results)

            else:
                self._print_error(f"Unknown collection command: {command}")
                self._print_info("Type 'help' for available commands")

        except SyntaxError as e:
            self._print_error(f"Syntax error: {e}")
            self._print_info("Check your command syntax")
        except NexaDBException as e:
            self._print_error(f"Database error: {e}")
        except Exception as e:
            self._print_error(f"Error: {e}")

    def run(self):
        """Run interactive CLI"""
        self.show_banner()

        if not self.connect():
            return

        print()

        while True:
            try:
                command = input(self._get_prompt())
                if not self.execute_command(command):
                    break
            except KeyboardInterrupt:
                print()
                self._print_info("Use 'exit' to quit")
            except EOFError:
                print()
                break


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='NexaDB Interactive CLI')
    parser.add_argument('--host', default='localhost', help='NexaDB host (default: localhost)')
    parser.add_argument('--port', type=int, default=6969, help='NexaDB port (default: 6969)')
    parser.add_argument('--api-key', default='',
                       help='API key (not required for localhost)')

    args = parser.parse_args()

    cli = NexaDBCLI(host=args.host, port=args.port, api_key=args.api_key)
    cli.run()


if __name__ == '__main__':
    main()
