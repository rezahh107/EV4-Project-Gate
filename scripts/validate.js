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
  'scripts/check-capability-truth.py',
  'scripts/check-workflow-permissions.py',
  'src/ev4_transition/data/capability-status.v1.json',
  '.github/workflows/status-after-merge.yml'
];

for (const path of requiredFiles) {
  if (!fs.existsSync(path)) {
    console.error(`Missing required file: ${path}`);
    process.exit(1);
  }
}

function assertExactCapability(actual, expected, label) {
  if (!actual || typeof actual !== 'object' || Array.isArray(actual)) {
    console.error(`${label} capability truth is missing or is not an object.`);
    process.exit(1);
  }

  const actualKeys = Object.keys(actual).sort();
  const expectedKeys = Object.keys(expected).sort();
  if (actualKeys.length !== expectedKeys.length || actualKeys.some((key, index) => key !== expectedKeys[index])) {
    console.error(`${label} capability truth has an unexpected field set.`);
    process.exit(1);
  }

  for (const key of expectedKeys) {
    if (actual[key] !== expected[key]) {
      console.error(`${label} capability truth is incorrect for ${key}.`);
      process.exit(1);
    }
  }
}

const capability = JSON.parse(fs.readFileSync('src/ev4_transition/data/capability-status.v1.json', 'utf8'));
const capabilities = capability.capabilities || {};

assertExactCapability(capabilities.ce_to_builder, {
  orchestration_baseline: 'implemented',
  cli_exposure: 'not_implemented',
  owner_fixture_integration: 'verified',
  real_non_synthetic_handoff: 'insufficient_evidence'
}, 'CE-to-Builder');

assertExactCapability(capabilities.builder_to_responsive, {
  orchestration_baseline: 'implemented',
  cli_exposure: 'not_implemented',
  owner_contract_lock: 'computed_from_pinned_owner_file_bytes',
  official_responsive_validator_integration: 'implemented',
  verification_state: 'verified_by_exact_head_ci',
  real_non_synthetic_handoff: 'insufficient_evidence'
}, 'Builder-to-Responsive');

assertExactCapability(capabilities.final_evidence_gate, {
  orchestration_baseline: 'implemented',
  cli_exposure: 'not_implemented',
  prior_lock_chain: 'pinned_to_immutable_project_gate_commit',
  official_responsive_validator_integration: 'implemented',
  verification_state: 'verified_by_exact_head_ci',
  real_non_synthetic_evidence: 'insufficient_evidence'
}, 'Final Evidence Gate');

const publicTransitions = capability.public_cli_transitions || [];
for (const transition of ['ce-to-builder', 'builder-to-responsive', 'final-evidence-gate']) {
  if (publicTransitions.includes(transition)) {
    console.error(`${transition} must not be exposed as a public CLI transition.`);
    process.exit(1);
  }
}

const syntaxCheck = spawnSync(process.execPath, ['--check', 'scripts/update-status-after-merge.js'], {
  encoding: 'utf8'
});

if (syntaxCheck.status !== 0) {
  process.stderr.write(syntaxCheck.stderr || syntaxCheck.stdout);
  process.exit(syntaxCheck.status || 1);
}

const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
const pythonChecks = [
  'scripts/check-capability-truth.py',
  'scripts/check-workflow-permissions.py',
  'scripts/check-github-action-pinning.py'
];

for (const script of pythonChecks) {
  const completed = spawnSync(pythonCmd, [script], { encoding: 'utf8' });
  if (completed.status !== 0) {
    process.stderr.write(completed.stderr || completed.stdout);
    process.exit(completed.status || 1);
  }
  process.stdout.write(completed.stdout);
}

console.log('Project Gate capability truth, workflow permissions, historical ledger automation, and workflow action pins are valid.');
