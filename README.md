# Expense Tracker — DevOps Pipeline

App code provided externally — all infrastructure, CI/CD, and deployment work is mine.

## Stage: Ansible
**What was built:**
Playbook to prepare the servers: Docker + k3s + GitHub Actions runner (systemd service)

**How it works:**
Describes the desired state, not commands — idempotent via `creates`, safe to re-run any time. Same playbook provisioned the second VM.

## Stage: Kubernetes
**What was built:**
k3s cluster, Deployment with 2 replicas, NodePort Service

**How it works:**
The Deployment pulls the image from GHCR and keeps 2 replicas running; the NodePort Service load-balances traffic across them.

## Stage: CI/CD
**What was built:**
GitHub Actions pipeline with a self-hosted runner

**How it works:**
On push → GitHub builds the image → pushes to GHCR (tagged with commit SHA) → self-hosted runner pulls and redeploys via `kubectl set image` → rolling update, zero downtime.