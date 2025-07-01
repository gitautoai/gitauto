def create_reset_command_message(branch_name: str) -> str:
    return f"""

---

If GitAuto's commits are not satisfactory, you can reset to your original state from your local branch:

```bash
git checkout {branch_name}
git push --force-with-lease origin {branch_name}
```
"""
