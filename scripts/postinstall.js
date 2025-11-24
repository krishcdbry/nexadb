#!/usr/bin/env node

/**
 * Post-install script for NexaDB npm package
 *
 * Checks system requirements and displays welcome message
 */

const { execSync } = require('child_process');

console.log('\n' + '='.repeat(70));
console.log('NexaDB Installation');
console.log('='.repeat(70));

// Check Python version
function checkPython() {
  const pythonCommands = ['python3', 'python'];

  for (const cmd of pythonCommands) {
    try {
      const version = execSync(`${cmd} --version`, {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe']
      });

      const match = version.match(/Python (\d+)\.(\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);

        if (major === 3 && minor >= 8) {
          console.log(`✓ Python ${match[0]} found (${cmd})`);
          return true;
        }
      }
    } catch (e) {
      continue;
    }
  }

  return false;
}

// Main check
const hasPython = checkPython();

if (!hasPython) {
  console.log('\n⚠  WARNING: Python 3.8+ not found!');
  console.log('   NexaDB requires Python 3.8 or higher.');
  console.log('   Download from: https://www.python.org/downloads/');
  console.log('');
} else {
  console.log('✓ All requirements met!');
  console.log('');
}

console.log('Quick Start:');
console.log('  1. Start database server:  npx nexadb-server');
console.log('  2. Start admin UI:         npx nexadb-admin');
console.log('  3. Open browser:           http://localhost:9999');
console.log('');
console.log('Commands:');
console.log('  nexadb-server    Start database server (port 6969)');
console.log('  nexadb-admin     Start admin UI (port 9999)');
console.log('  nexadb --help    Show all commands');
console.log('');
console.log('Documentation:');
console.log('  Installation:    INSTALLATION.md');
console.log('  Quick Start:     README.md');
console.log('  Deployment:      DEPLOY_*.md');
console.log('');
console.log('='.repeat(70));
console.log('\n');
