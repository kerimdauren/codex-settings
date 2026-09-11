---
name: b3-post-push-rollout
description: Use after pushing a Biometry 3.0 service change or release to preflight PROD secrets, then verify GitLab CI, image-tag propagation, Rancher/Kubernetes rollout, Ready state, and startup logs.
argument-hint: "[service] [environment]"
disable-model-invocation: true
user-invocable: false
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
---

# B3 Post-push Rollout

## When to use

Use after source changes have been pushed for a `b3-*` service, or for an explicit B3 release task.

Do not use when the user limits the task to source code or explicitly forbids changes to GitLab manifests, Rancher, or Kubernetes.

## Inputs / context to gather

1. Confirm the actual service checkout, pushed commit/branch, target environment, GitLab pipeline, manifest location, and Rancher/Kubernetes workload.
2. Confirm whether manifest and Rancher changes are in scope; source-only scope overrides this procedure.
3. For PROD rollout, require explicit approval immediately before promotion only for `b3-beedoc`, `b3-liveness`, and `b3-beeface`. For every other B3 service, do not pause for separate rollout approval when promotion is already within the user's authorized scope.
4. For PROD only, identify required target-secret keys and verify their presence without printing values. If a value is missing, inspect another B3 service only for a clearly applicable source; if value or purpose is uncertain, report the exact source/target keys and obtain explicit approval before changing secrets.
5. Record the pre-rollout image tag/revision so the new deployment can be proved rather than assumed.

## Procedure

1. For PROD, complete the secret preflight and any service-specific rollout approval before promotion or merge to `main`.
2. After push, check the corresponding GitLab CI pipeline and wait for its completed status.
3. On a successful build, check whether the generated build number/image tag has propagated to the GitLab manifest or Rancher.
4. If it has not updated automatically within two minutes, inspect the authoritative GitOps values repository and Argo status. Only if manifest change is in scope and authorized, make the smallest reviewed values-manifest change.
5. Wait briefly, then verify the Rancher/Kubernetes rollout, deployed image tag, and that a pod from the new revision started and is `Ready`.
6. Inspect startup logs from that new Ready pod for normal initialization.
7. When the change adds a runtime endpoint, metric, or observable contract, verify that evidence from the new pod/environment too; startup alone is not proof that the change is live.
8. Never mutate the live deployment image directly. If GitOps remains stale, report the exact authoritative manifest and pending approved change, or make only the authorized values-manifest change, then repeat the rollout, `Ready`, and startup-log checks.
9. If CI or startup logs show an error, investigate the root cause, make the smallest in-scope fix, push/deploy it, and repeat the full CI-to-Ready-and-logs loop. Stop only for a required user decision, missing access, or external dependency that prevents safe progress.

## Efficiency plan

1. Start from the pushed commit and pipeline link; do not rediscover the service from broad workspace scans.
2. Cache the old and expected image tags, then use those exact strings for manifest, Rancher, and pod checks.
3. Use the two-minute propagation boundary as the switch from observation to authoritative-values/Argo inspection.
4. Do not perform local Docker builds; CI is the build authority for B3.
5. Treat secret values as non-output data: verify key presence/equality only, and do not copy a PROD value on uncertain semantic match.

## Pitfalls and fixes

1. Symptom: a successful pipeline is reported as deployment completion.
   - Likely cause: image-tag propagation and pod revision were assumed.
   - Fix: prove deployed tag, rollout, and `Ready` on a new pod revision.
2. Symptom: the new build never appears in Rancher.
   - Likely cause: automatic manifest or Rancher image-tag propagation stalled.
   - Fix: after two minutes inspect Argo and the authoritative values repo; make only an authorized reviewed values-manifest change, never a live deployment mutation.
3. Symptom: rollout remediation exceeds the user's requested edit boundary.
   - Likely cause: source-only scope or an explicit manifest/Rancher prohibition was missed.
   - Fix: stop at the boundary and report the exact pending deployment action.
4. Symptom: a PROD secret is copied from another service without confidence.
   - Likely cause: name similarity was mistaken for the same purpose.
   - Fix: state the exact source and target key and obtain user approval before changing the secret.

## Verification checklist

1. The pushed commit has a completed GitLab CI result.
2. The expected image tag is visible in the target manifest or Rancher workload.
3. The workload rolled out a new revision using that tag.
4. A pod from the new revision started successfully and is `Ready`.
5. Startup logs from that Ready pod show normal initialization.
6. Any changed endpoint, metric, or runtime contract has environment-specific proof when applicable.
7. For PROD, rollout approval was obtained before promotion for `b3-beedoc`, `b3-liveness`, or `b3-beeface`; no separate rollout approval was requested for another service.
8. For PROD, every required target-secret key was verified before promotion; uncertain copies were approved explicitly.
9. Any failure was either remediated by a smallest in-scope fix and re-verified, or reported as a concrete decision/access/external blocker.
