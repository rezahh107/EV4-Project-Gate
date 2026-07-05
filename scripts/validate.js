const fs = require('fs');
const { spawnSync } = require('child_process');

const requiredFiles = [
  'README.md',
  'AGENTS.md',
  'docs/IMPLEMENTATION_STATUS.yaml',
  'docs/EV4_SHARED_CONTRACTS_STATUS.md',
  'docs/ROLE_BOUNDARY_MAP.md',
  'docs/CONTRACT_INVENTORY.md',
  'docs/COMPATIBILITY_MAP.md',
  'docs/MIGRATION_READINESS_CHECKLIST.md',
  'docs/VALIDATION_STRATEGY.md',
  'docs/PROMOTION_RULES.md',
  'docs/ADR/0001-non-authoritative-skeleton.md',
  'schemas/README.md',
  'fixtures/README.md',
  'scripts/README.md',
  'scripts/update-status-after-merge.js',
  'scripts/check-github-action-pinning.py',
  'src/ev4_transition/data/capability-status.v1.json',
  '.github/workflows/status-after-merge.yml'
];

for (const path of requiredFiles) {
  if (!fs.existsSync(path)) {
    console.error(`Missing required file: ${path}`);
    process.exit(1);
  }
}

const capability = JSON.parse(fs.readFileSync('src/ev4_transition/data/capability-status.v1.json', 'utf8'));
const c2b = capability.capabilities && capability.capabilities.ce_to_builder;
const expectedC2b = {
  orchestration_baseline: 'implemented',
  cli_exposure: 'not_implemented',
  owner_fixture_integration: 'verified',
  real_non_synthetic_handoff: 'insufficient_evidence'
};

if (JSON.stringify(c2b) !== JSON.stringify(expectedC2b)) {
  console.error('CE-to-Builder capability truth is missing or incorrect.');
  process.exit(1);
}

if ((capability.public_cli_transitions || []).includes('ce-to-builder')) {
  console.error('CE-to-Builder must not be exposed as a public CLI transition.');
  process.exit(1);
}

const syntaxCheck = spawnSync(process.execPath, ['--check', 'scripts/update-status-after-merge.js'], {
  encoding: 'utf8'
});

if (syntaxCheck.status !== 0) {
  process.stderr.write(syntaxCheck.stderr || syntaxCheck.stdout);
  process.exit(syntaxCheck.status || 1);
}

const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
const pinCheck = spawnSync(pythonCmd, ['scripts/check-github-action-pinning.py'], {
  encoding: 'utf8'
});

if (pinCheck.status !== 0) {
  process.stderr.write(pinCheck.stderr || pinCheck.stdout);
  process.exit(pinCheck.status || 1);
}

process.stdout.write(pinCheck.stdout);
console.log('Project Gate skeleton, capability truth, historical ledger automation, and workflow action pins are valid.');
