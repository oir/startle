"""
This example illustrates how to use the **kwargs argument.

Requires the `requests` package to be installed.

Example invocations:
    python examples/request.py "machine learning"
    python examples/request.py "data science" --sort stars
    python examples/request.py "web development" --sort stars --order desc
    python examples/request.py "web development" --sort stars --order asc
"""

import requests

from startle import start


def search_repos(query: str = "language:python", **kwargs):
    """
    Search GitHub's repositories for a query.

    Adapted from https://realpython.com/python-requests/#query-string-parameters.

    Args:
        query: The query to search for.
        **kwargs: Additional query string parameters.
    """
    params = {"q": query} | kwargs
    print(f"Request parameters: {params}")
    print()

    response = requests.get("https://api.github.com/search/repositories", params=params)

    # Inspect some attributes of the first five repositories
    json_response = response.json()
    popular_repositories = json_response["items"]
    for repo in popular_repositories[:5]:
        print(f"Name: {repo['name']}")
        print(f"Description: {repo['description']}")
        print(f"Stars: {repo['stargazers_count']}")
        print()


if __name__ == "__main__":
    start(search_repos)
