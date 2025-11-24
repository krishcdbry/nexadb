#!/usr/bin/env node

/**
 * NexaDB Server - Node.js wrapper for Python server
 *
 * This script starts the NexaDB Python server.
 * It checks for Python 3.8+ and launches nexadb_server.py
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Check if Python is installed
function findPython() {
  const pythonCommands = ['python3', 'python'];

  for (const cmd of pythonCommands) {
    try {
      const result = require('child_process').execSync(`${cmd} --version`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });

      // Check version (need 3.8+)
      const match = result.match(/Python (\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);

        if (major === 3 && minor >= 8) {
          return cmd;
        }
      }
    } catch (e) {
      // Command not found, try next
      continue;
    }
  }

  return null;
}

// Main
const pythonCmd = findPython();

if (!pythonCmd) {
  console.error('Error: Python 3.8 or higher is required');
  console.error('Please install Python from: https://www.python.org/downloads/');
  process.exit(1);
}

// Find the server script
const scriptDir = path.join(__dirname, '..');
const serverScript = path.join(scriptDir, 'nexadb_server.py');

if (!fs.existsSync(serverScript)) {
  console.error(`Error: nexadb_server.py not found at ${serverScript}`);
  process.exit(1);
}

// Parse arguments
const args = process.argv.slice(2);

// Start the server
console.log('Starting NexaDB server...');
console.log(`Using Python: ${pythonCmd}`);

const server = spawn(pythonCmd, [serverScript, ...args], {
  cwd: scriptDir,
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONUNBUFFERED: '1'
  }
});

server.on('error', (err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});

server.on('exit', (code, signal) => {
  if (code !== 0 && code !== null) {
    console.error(`Server exited with code ${code}`);
    process.exit(code);
  }
  if (signal) {
    console.log(`Server terminated by signal ${signal}`);
    process.exit(1);
  }
});

// Handle Ctrl+C
process.on('SIGINT', () => {
  console.log('\nShutting down server...');
  server.kill('SIGINT');
  setTimeout(() => {
    server.kill('SIGTERM');
  }, 1000);
});

process.on('SIGTERM', () => {
  server.kill('SIGTERM');
});
