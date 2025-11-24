#!/usr/bin/env node

/**
 * NexaDB Admin UI - Node.js wrapper for Python admin server
 *
 * This script starts the NexaDB Admin UI server.
 * It checks for Python 3.8+ and launches nexadb_admin_server.py
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

// Find the admin script
const scriptDir = path.join(__dirname, '..');
const adminScript = path.join(scriptDir, 'nexadb_admin_server.py');

if (!fs.existsSync(adminScript)) {
  console.error(`Error: nexadb_admin_server.py not found at ${adminScript}`);
  process.exit(1);
}

// Parse arguments
const args = process.argv.slice(2);

// Start the admin UI
console.log('Starting NexaDB Admin UI...');
console.log(`Using Python: ${pythonCmd}`);

const admin = spawn(pythonCmd, [adminScript, ...args], {
  cwd: scriptDir,
  stdio: 'inherit',
  env: {
    ...process.env,
    PYTHONUNBUFFERED: '1'
  }
});

admin.on('error', (err) => {
  console.error('Failed to start admin UI:', err);
  process.exit(1);
});

admin.on('exit', (code, signal) => {
  if (code !== 0 && code !== null) {
    console.error(`Admin UI exited with code ${code}`);
    process.exit(code);
  }
  if (signal) {
    console.log(`Admin UI terminated by signal ${signal}`);
    process.exit(1);
  }
});

// Handle Ctrl+C
process.on('SIGINT', () => {
  console.log('\nShutting down admin UI...');
  admin.kill('SIGINT');
  setTimeout(() => {
    admin.kill('SIGTERM');
  }, 1000);
});

process.on('SIGTERM', () => {
  admin.kill('SIGTERM');
});
