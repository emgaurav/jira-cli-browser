import requests
from requests.auth import HTTPBasicAuth
from getpass import getpass
import sys
import select 

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

def download_confluence_page(jira_domain, jira_email, jira_api_token, page_id):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    headers = {'Accept': 'application/json'}
    url = f"https://{jira_domain}/wiki/rest/api/content/{page_id}?expand=body.storage"

    response = requests.get(url, auth=auth, headers=headers)
    if response.ok:
        page_data = response.json()
        page_content = page_data['body']['storage'].get('value', None)

        if page_content:
            with open(f"Confluence_Page_{page_id}.html", 'w', encoding='utf-8') as file:
                file.write(page_content)
            print(colored(f"Page {page_id} downloaded successfully.", GREEN_COLOR))
        else:
            print(colored("Received data but no page content found. Here's the received data for diagnostics:", RED_COLOR))
            print(page_data)  # Print the received JSON for diagnostics
    else:
        print(colored("Failed to download the page. Here's why:", RED_COLOR))
        print(response.text)  # This will print the raw response for debugging

# Integrate the updated function into your main script as before.

def list_confluence_spaces(jira_domain, jira_email, jira_api_token):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    response = requests.get(f"https://{jira_domain}/wiki/rest/api/space", auth=auth)
    spaces = response.json().get('results', []) if response.ok else []
    print("Confluence spaces:")
    for space in spaces:
        print(f"- {space['name']} (Key: {space['key']})")

def list_confluence_parent_pages(jira_domain, jira_email, jira_api_token, space_key):
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    headers = {'Accept': 'application/json'}

    start_at = 0
    limit = 100  # Number of results per page
    top_level_parents = []

    print("Press 'Enter' at any time to stop and proceed with the pages found so far.")

    try:
        while True:
            url = f"https://{jira_domain}/wiki/rest/api/content?spaceKey={space_key}&type=page&status=current&start={start_at}&limit={limit}&expand=ancestors"
            response = requests.get(url, auth=auth, headers=headers, timeout=10)
            if not response.ok:
                print("Failed to fetch pages. Status: {}, Message: {}".format(response.status_code, response.text))
                return

            data = response.json()
            pages = data.get('results', [])
            for page in pages:
                ancestors = page.get('ancestors', [])
                if len(ancestors) <= 1:  # Check if the page has 0 or 1 ancestor
                    top_level_parents.append(page)
                    print(f"\nFound top-level parent: {page['title']} (ID: {page['id']})", end='')

            # Check for user input to stop early
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = input()
                break

            # Update progress without a newline
            sys.stdout.write(f"\rChecked {start_at + limit} pages, found {len(top_level_parents)} top-level parents so far...")
            sys.stdout.flush()

            if 'next' in data['_links']:
                start_at += limit
            else:
                break

        print("\n\nTop-level parent pages:")
        for i, page in enumerate(top_level_parents):
            print(f"{i + 1}. {page['title']} (ID: {page['id']})")

        # Prompt user to select a parent page
        print("\nEnter the number of the parent page to list its child pages, or '0' to return to the menu:")
        selection = input("Your choice: ").strip()
        if selection.isdigit():
            selection = int(selection)
            if selection == 0:
                print("Returning to the main menu.")
                return
            elif 1 <= selection <= len(top_level_parents):
                selected_parent_id = top_level_parents[selection - 1]['id']
                list_all_child_pages(jira_domain, jira_email, jira_api_token, selected_parent_id)
            else:
                print("Invalid selection. Please try again.")
        else:
            print("Please enter a valid number.")

    except requests.exceptions.Timeout:
        print(colored("Request timed out. Please try again later.", RED_COLOR))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user. Returning to menu.")

def list_all_child_pages(jira_domain, jira_email, jira_api_token, page_id, indent=0):
    """
    Recursively lists all child pages of a given page.
    """
    auth = HTTPBasicAuth(jira_email, jira_api_token)
    headers = {'Accept': 'application/json'}
    url = f"https://{jira_domain}/wiki/rest/api/content/{page_id}/child/page"

    response = requests.get(url, auth=auth, headers=headers)
    if response.ok:
        child_pages = response.json().get('results', [])
        for child in child_pages:
            title = child['title']
            child_id = child['id']
            print(" " * indent + f"- {title} (ID: {child_id})")
            list_all_child_pages(jira_domain, jira_email, jira_api_token, child_id, indent + 2)
    else:
        print("Failed to fetch child pages for page ID: {}".format(page_id))

def main():
    try:
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
            print("8. Download a Confluence page")
            print((colored("0. Exit", RED_COLOR)))
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
                list_confluence_parent_pages(jira_domain, jira_email, jira_api_token, space_key)
            elif choice == '6':
                list_filters(jira_domain, jira_email, jira_api_token)
            elif choice == '8':
                page_id = input("Enter the Confluence page ID: ")
                download_confluence_page(jira_domain, jira_email, jira_api_token, page_id)
            elif choice == '7':
                filter_id = input("Enter filter ID: ")
                list_issues_by_filter(jira_domain, jira_email, jira_api_token, filter_id)
            elif choice == '0':
                break
            else:
                print(colored("Invalid option.", RED_COLOR))
    except KeyboardInterrupt:
        print("\nCtrl+C pressed. Exiting...")
        sys.exit(0)
        
if __name__ == "__main__":
    main()
