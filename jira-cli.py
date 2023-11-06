import requests
from requests.auth import HTTPBasicAuth
from getpass import getpass

# Color codes
GREEN_COLOR = '\033[92m'
BLUE_COLOR = '\033[94m'
RED_COLOR = '\033[91m'
END_COLOR = '\033[0m'

def colored(text, color):
    return f"{color}{text}{END_COLOR}"

def validate_token(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(f"https://{jira_domain}/rest/api/3/myself", auth=auth)
    return response.status_code == 200

def check_service_availability(jira_domain, service_path, auth):
    response = requests.get(f"https://{jira_domain}/{service_path}", auth=auth)
    return response.ok

def list_services(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    print("Services accessible:")
    if check_service_availability(jira_domain, "rest/api/3/project", auth):
        print("- Jira Software")
    if check_service_availability(jira_domain, "wiki/rest/api/space", auth):
        print("- Confluence")

def list_projects(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(f"https://{jira_domain}/rest/api/3/project", auth=auth)
    projects = response.json() if response.ok else []
    print("Projects accessible:")
    for project in projects:
        print(f"- {project['name']} (Key: {project['key']})")

def list_issues(jira_domain, jira_email, jira_api_token, project_key):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    start_at = 0
    max_results = 50  # Adjust as needed
    total_issues_fetched = 0

    while True:
        response = requests.get(
            f"https://{jira_domain}/rest/api/3/search?jql=project={project_key}&startAt={start_at}&maxResults={max_results}",
            auth=auth
        )
        data = response.json() if response.ok else {}
        total = data.get('total', 0)
        issues = data.get('issues', [])
        print(f"Issues in project {project_key}:")

        for issue in issues:
            issue_link = f"https://{jira_domain}/browse/{issue['key']}"
            print(f"- {issue['fields']['summary']} (ID: {issue['id']}) - Link: {issue_link}")
        
        total_issues_fetched += len(issues)
        if total_issues_fetched < total:
            more = input("More issues available. Load more? (y/n): ").lower()
            if more != 'y':
                break
            start_at += len(issues)
        else:
            break

def list_filters(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(
        f"https://{jira_domain}/rest/api/3/filter/search",
        auth=auth
    )
    data = response.json() if response.ok else {}
    filters = data.get('values', [])

    if filters:
        print("Filters:")
        for filter in filters:
            print(f"- {filter['name']} (ID: {filter['id']})")
    else:
        print("No filters found or unable to retrieve filters.")

def list_issues_by_filter(jira_domain, jira_email, jira_api_token, filter_id):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(
        f"https://{jira_domain}/rest/api/3/filter/{filter_id}",
        auth=auth
    )
    filter_data = response.json() if response.ok else {}
    jql = filter_data.get('jql', '')

    if jql:
        response = requests.get(
            f"https://{jira_domain}/rest/api/3/search?jql={jql}",
            auth=auth
        )
        data = response.json() if response.ok else {}
        issues = data.get('issues', [])
        print(f"Issues for filter {filter_id}:")
        for issue in issues:
            issue_link = f"https://{jira_domain}/browse/{issue['key']}"
            print(f"- {issue['fields']['summary']} (ID: {issue['id']}) - Link: {issue_link}")
    else:
        print(f"No JQL found for filter ID {filter_id} or unable to retrieve filter details.")



def list_confluence_spaces(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(f"https://{jira_domain}/wiki/rest/api/space", auth=auth)
    spaces = response.json().get('results', []) if response.ok else []
    print("Confluence spaces:")
    for space in spaces:
        print(f"- {space['name']} (Key: {space['key']})")

def list_confluence_space_docs(jira_domain, jira_email, jira_api_token, space_key):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(f"https://{jira_domain}/wiki/rest/api/content?spaceKey={space_key}", auth=auth)
    pages = response.json().get('results', []) if response.ok else []
    print(f"Documents in Confluence space {space_key}:")
    for page in pages:
        page_link = f"https://{jira_domain}/wiki{page['_links']['webui']}"
        print(f"- {page['title']} - Link: {page_link}")

def main():
    jira_domain = input("Enter your Jira domain (e.g., 'your-domain.atlassian.net'): ")
    jira_email = input("Enter your Jira email: ")
    jira_api_token = getpass("Enter your Jira API token: ")

    if not validate_token(jira_domain, jira_email, jira_api_token):
        print(colored("Invalid email or API token.", RED_COLOR))
        return

    auth = HTTPBasicAuth(jira_email, jira_api_token)

    while True:
        print(colored("\nChoose an option:", GREEN_COLOR))
        print("1. List services")
        print("2. List projects")
        print("3. List issues in a project")
        print("4. List Confluence spaces")
        print("5. List documents in a Confluence space")
        print("6. List all filters")
        print("7. List all issues in a filter")
        print((colored("8. Exit", RED_COLOR)))
        choice = input("Enter option (1-8): ")

        if choice == '1':
            list_services(jira_domain, jira_email, jira_api_token)
        elif choice == '2':
            list_projects(jira_domain, jira_email, jira_api_token)
        elif choice == '3':
            project_key = input("Enter the project key: ")
            list_issues(jira_domain, jira_email, jira_api_token, project_key)
        elif choice == '4':
            list_confluence_spaces(jira_domain, jira_email, jira_api_token)
        elif choice == '5':
            space_key = input("Enter Confluence space key: ")
            list_confluence_space_docs(jira_domain, jira_email, jira_api_token, space_key)
        elif choice == '6':
            list_filters(jira_domain, jira_email, jira_api_token)
        elif choice == '7':
            filter_id = input("Enter filter ID: ")
            list_issues_by_filter(jira_domain, jira_email, jira_api_token, filter_id)
        elif choice == '8':
            break
        else:
            print(colored("Invalid option.", RED_COLOR))

if __name__ == "__main__":
    main()
