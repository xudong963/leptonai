"""
Common utilities for the CLI.
"""

import sys

import click

from rich.console import Console
from leptonai.api import APIError
import leptonai.api.workspace as workspace


console = Console(highlight=False)


def click_group(*args, **kwargs):
    class ClickAliasedGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            rv = click.Group.get_command(self, ctx, cmd_name)
            if rv is not None:
                return rv

            def is_abbrev(x, y):
                # first char must match
                if x[0] != y[0]:
                    return False
                it = iter(y)
                return all(any(c == ch for c in it) for ch in x)

            matches = [x for x in self.list_commands(ctx) if is_abbrev(cmd_name, x)]

            if not matches:
                return None
            elif len(matches) == 1:
                return click.Group.get_command(self, ctx, matches[0])
            ctx.fail(f"'{cmd_name}' is ambiguous: {', '.join(sorted(matches))}")

        def resolve_command(self, ctx, args):
            # always return the full command name
            _, cmd, args = super().resolve_command(ctx, args)
            return cmd.name, cmd, args

    return click.group(*args, cls=ClickAliasedGroup, **kwargs)


def get_workspace_and_token_or_die():
    """
    Gets the workspace URL and auth token or exits if they are not found.

    :return: A tuple of the workspace URL and auth token.
    """
    workspace_url = workspace.get_workspace_url()
    if workspace_url is None:
        console.print("No workspace found. Please run `lep workspace login` first.")
        sys.exit(1)
    auth_token = workspace.get_auth_token(workspace_url)
    if auth_token is None:
        console.print("No auth token found. Please run `lep workspace login` first.")
        sys.exit(1)
    return workspace_url, auth_token


def check(condition, message):
    """
    Checks a condition and prints a message if the condition is false.

    :param condition: The condition to check.
    :param message: The message to print if the condition is false.
    """
    if not condition:
        console.print(message)
        sys.exit(1)


def guard_api(content_or_error, detail=False, msg=None):
    """
    A wrapper around API calls that exits if the call  prints an error message and exits if the call was unsuccessful.

    This is useful for CLI commands that call the API and need to handle errors.

    :param json_or_error: The json returned by the API call, or an APIError or NotJsonError.
    :param detail: If True, print the error message from the API call.
    :param msg: If not None, print this message instead of the error message from the API call.
    """
    if isinstance(content_or_error, APIError):
        if detail:
            console.print(content_or_error)
        if msg:
            console.print(msg)
        sys.exit(1)
    # If the above are not true, then the API call was successful, and we can return the json.
    return content_or_error


def explain_response(response, if_200, if_404, if_others, exit_if_404=False):
    """
    A wrapper function that prints a message based on the response status code.
    If the response status code is 200, print if_200, and return.
    If the response status code is 404, print if_404, and exit if exit_if_404 is true.
    If the response status code is anything else, print if_others and always exit(1).
    """
    if response.status_code == 200:
        console.print(if_200)
        return
    elif response.status_code == 404:
        console.print(if_404)
        if exit_if_404:
            sys.exit(1)
    else:
        console.print(if_others)
        sys.exit(1)
