# pre-commit-django
Pre-commit hooks for django projects

## How to Use
Add this to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/ryanmarquardt/pre-commit-django
    # Set rev according to the django version you want to check. Only 2.2 is supported at the moment.
    rev: django2.2
    hooks:
    -   id: django-migrations-exist
```

## Hooks

### django-migrations-exist

Checks that any changed models also have migrations staged for commit.
