"""Reusable building blocks for the story-automation workflow.

Public surface (stable):
- _actions:  plain Python functions wrapping xlsx + Azure DevOps REST.
- _tools:    @tool wrappers over _actions for use by an Agent.
- _secrets:  Azure Key Vault fetch helper.
- _agent:    Agent factory + system prompt.
"""
