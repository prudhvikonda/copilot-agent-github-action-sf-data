# AI-Assisted Salesforce Data Deployment POC

## Solution Overview
This repository provides a complete proof of concept for AI-assisted Salesforce data deployment using GitHub Actions, a GitHub Copilot Agent definition, Salesforce CLI, and OAuth 2.0 Client Credentials Flow. The workflow processes a CSV file from the data folder, transforms it into a Salesforce-ready import file, and loads Account records into Salesforce after an environment approval gate.

## Architecture Overview
- GitHub Actions orchestrates the deployment lifecycle.
- A GitHub Environment named PROD enforces approval before Salesforce operations begin.
- A Copilot Agent definition documents the transformation intent and expected output.
- Python scripts validate, transform, and generate audit artifacts.
- Shell scripts authenticate to Salesforce and perform the data import.

## Repository Structure
- .github/workflows/salesforce-data-load.yml
- .copilot/agents/account-data-transformer.md
- scripts/authenticate-salesforce.sh
- scripts/transform-accounts.py
- scripts/load-accounts.sh
- scripts/generate-audit-report.py
- data/account-names.csv
- artifacts/
- README.md

## Prerequisites
- A GitHub repository with Actions enabled.
- A Salesforce org with a Connected App configured for OAuth 2.0 Client Credentials Flow.
- Salesforce CLI installed locally for testing.
- Python 3.11+.

## Salesforce Connected App Setup
1. Create a Connected App in Salesforce Setup.
2. Enable OAuth Settings.
3. Enable the Client Credentials Flow.
4. Configure the callback URL if required by your org policy.
5. Grant the app API Enabled and Account object create permissions.
6. Assign the Connected App to an integration user.

## Client Credentials Flow Setup
Create a dedicated integration user and configure the Connected App to run as that user. Ensure the integration user has permission to create Accounts and access the API.

## Salesforce Integration User Setup
The integration user should have:
- API Enabled
- Create on Account
- Read on Account
- View All Data or appropriate object-level sharing

## GitHub Environment Setup
Create a GitHub Environment named PROD in the repository settings. Add required reviewers to enforce manual approvals.

## GitHub Environment Protection Rule Setup
Configure the PROD environment with:
- Required reviewers
- Deployment branches restricted to main
- Approval required before execution continues

## GitHub Secrets Configuration
Add the following repository or environment secrets:
- SF_CLIENT_ID
- SF_CLIENT_SECRET
- SF_LOGIN_URL

The workflow uses these values securely and never prints them to logs.

## Workflow Execution Process
1. A pull request is merged into main or workflow_dispatch is used.
2. The workflow checks prerequisites and validates the input CSV.
3. The PROD environment approval gate pauses execution until an approver approves.
4. The transformation script produces a Salesforce-ready CSV.
5. Salesforce CLI authenticates non-interactively using OAuth 2.0 Client Credentials Flow.
6. The load script inserts Accounts into Salesforce.
7. Audit and import artifacts are generated and uploaded.

## Copilot Agent Design
The Copilot Agent definition in .copilot/agents/account-data-transformer.md describes the transformation intent for the repository. The workflow invokes the transformation script, which reads the data file and creates the output artifacts.

## Data Transformation Logic
The transformation script:
- Reads data/account-names.csv
- Removes blank entries
- Detects duplicate names
- Excludes invalid records
- Maps AccountName to Name
- Adds Industry = Media
- Writes artifacts/transformed-accounts.csv

## Salesforce Import Process
The load script uses Salesforce CLI to insert Accounts and records the results in artifacts/salesforce-import-results.json.

## Artifact Descriptions
- artifacts/transformed-accounts.csv: Salesforce-ready import data
- artifacts/transformation-summary.json: transformation counts and duplicate information
- artifacts/salesforce-import-results.json: per-record import outcomes
- artifacts/audit-report.json: final deployment audit details
- artifacts/execution.log: workflow and script execution log

## Logging Strategy
Every key stage writes to artifacts/execution.log and the supporting transformation log.

## Audit Strategy
The audit report captures workflow metadata, approval context, source file details, records processed, and import outcomes for traceability.

## Security Considerations
- Do not store secrets in source code.
- Use GitHub Secrets and GitHub Environments.
- Avoid printing tokens or credentials in logs.
- Use least-privilege integration permissions.

## Operational Considerations
- Retry transient API failures where appropriate.
- Review the generated artifacts after each run.
- Keep the integration user dedicated for automation.

## Troubleshooting Guide
- If the workflow fails before authentication, verify GitHub Secrets are present.
- If Salesforce import fails, confirm the Connected App and user permissions.
- If the CSV is empty or malformed, validate the header and values.

## Testing Instructions
Run the transformation script locally:
python3 scripts/transform-accounts.py --input data/account-names.csv --output artifacts/transformed-accounts.csv --summary artifacts/transformation-summary.json --log artifacts/transformation.log --agent-spec .copilot/agents/account-data-transformer.md

Run the audit generator locally:
python3 scripts/generate-audit-report.py --summary artifacts/transformation-summary.json --import-results artifacts/salesforce-import-results.json --audit-file artifacts/audit-report.json --workflow-name demo --workflow-run-id 1 --trigger manual --github-user demo --pr-number 1 --commit-sha local --approver demo --source-file data/account-names.csv --org-alias prod-integration --instance-url https://login.salesforce.com --log-file artifacts/execution.log

## Example Execution Walkthrough
1. Add or update data/account-names.csv.
2. Open a pull request to main.
3. Merge the PR.
4. Approve the PROD environment deployment.
5. Review the generated artifacts.

## Future Enhancements
- Support bulk API imports.
- Add data quality rules and validation thresholds.
- Extend the agent to support more complex transformation mappings.
