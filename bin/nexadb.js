#!/usr/bin/env node

/**
 * NexaDB CLI - Main entry point
 *
 * Shows help and available commands
 */

const { execSync } = require('child_process');
const path = require('path');

const args = process.argv.slice(2);

// Show help
if (args.length === 0 || args[0] === '--help' || args[0] === '-h') {
  console.log(`
NexaDB - Zero-dependency LSM-Tree database

Usage:
  nexadb <command> [options]

Commands:
  server              Start the database server
  admin               Start the admin UI
  help                Show this help message

Shortcuts:
  nexadb-server       Same as 'nexadb server'
  nexadb-admin        Same as 'nexadb admin'

Examples:
  nexadb server       Start database server on port 6969
  nexadb admin        Start admin UI on port 9999

For more information:
  https://github.com/yourusername/nexadb
`);
  process.exit(0);
}

// Execute command
const command = args[0];

if (command === 'server') {
  const serverScript = path.join(__dirname, 'nexadb-server.js');
  require(serverScript);
} else if (command === 'admin') {
  const adminScript = path.join(__dirname, 'nexadb-admin.js');
  require(adminScript);
} else if (command === 'help' || command === '--help' || command === '-h') {
  execSync('node ' + __filename + ' --help', { stdio: 'inherit' });
} else {
  console.error(`Unknown command: ${command}`);
  console.error('Use "nexadb --help" for available commands');
  process.exit(1);
}
