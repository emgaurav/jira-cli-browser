# jira-cli-browser
A full fledged jira and confluence browser on your CLI

## Description
This CLI tool is designed to interact with Jira's API to perform various tasks such as listing projects, issues, and filters, checking Jira and Confluence services, and much more, directly from the command line.

## Use Cases
- **Leaked Credentials:** If you're a pentester and you've found leaked Jira credentials, you can use this tool to quickly assess the access level of the compromised account.
- **Project Management:** Project managers can swiftly navigate through projects, issues, and filters to monitor progress or generate reports.
- **Automation:** Developers and system admins can integrate this CLI tool into their scripts to automate Jira interactions.
- **Audit:** Security teams can audit Jira projects and issues for compliance and access controls.

## Features
- Validate Jira API tokens.
- List accessible Jira Software services and Confluence spaces.
- Enumerate all projects available to the user.
- Display all issues in a specified project.
- List all user-accessible filters and associated issues.

## Quick Start
1. Clone the repository.
2. Install any necessary dependencies (e.g., `requests` library).
3. Run the script in your terminal: `python jira-cli.py`.
4. Follow the interactive menu to navigate through your Jira instance.

## Contributing
Contributions, issues, and feature requests are welcome. Feel free to check [issues page](#) if you want to contribute.

