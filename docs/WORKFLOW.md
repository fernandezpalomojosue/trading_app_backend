# GitHub Actions Workflow Architecture

## 🔄 CI/CD Flow

### **Current Architecture**

```
Pull Request → CI Workflow → Auto-Merge → Deploy Workflow → Render
```

### **Why `workflow_run` instead of `push`?**

**The Problem:**
- GitHub Actions using `GITHUB_TOKEN` cannot trigger other workflows
- This prevents infinite loops and recursive execution
- Auto-merge happens with `GITHUB_TOKEN` → push workflow never triggered

**The Solution:**
- Use `workflow_run` trigger to detect when CI completes
- Only runs if CI was successful (`conclusion == 'success'`)
- Clean separation of concerns

---

## 📋 Workflow Files

### **1. `.github/workflows/pr-merge.yml` (CI)**
```yaml
name: CI
on:
  pull_request:
    branches: [master]
```

**Purpose:**
- Run tests on pull requests
- Auto-merge if tests pass
- Trigger deployment workflow

### **2. `.github/workflows/master-push.yml` (Deploy)**
```yaml
name: Deploy to Production
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
    branches: [master]
```

**Purpose:**
- Trigger after successful CI
- Log deployment information
- Signal Render to auto-deploy

---

## 🚀 Flow Sequence

### **Step 1: Pull Request**
```bash
git checkout -b feature/new-endpoint
git push origin feature/new-endpoint
# Create PR → triggers CI workflow
```

### **Step 2: CI Workflow**
```yaml
# Runs tests
# If successful → auto-merge
# Triggers deploy workflow
```

### **Step 3: Deploy Workflow**
```yaml
# Triggered by workflow_run
# Only if CI succeeded
# Signals Render
```

### **Step 4: Render Deployment**
- Detects GitHub Actions completion
- Runs `render_migrate.py`
- Deploys new version

---

## 🔧 Configuration Details

### **Auto-Merge Conditions**
```javascript
// In CI workflow
if (context.payload.pull_request.mergeable &&
    context.payload.pull_request.mergeable_state === 'clean') {
  await github.rest.pulls.merge({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: context.payload.pull_request.number,
    merge_method: 'merge'
  });
}
```

### **Deploy Trigger Conditions**
```yaml
# In Deploy workflow
if: ${{ github.event.workflow_run.conclusion == 'success' }}
```

---

## 🎯 Benefits

### **✅ Clean Architecture**
- **Separation of concerns**: Testing vs Deployment
- **No infinite loops**: Protected by GitHub
- **Reliable triggering**: `workflow_run` is guaranteed

### **✅ Debugging**
- **Clear logs**: Each workflow has specific purpose
- **Easy troubleshooting**: Can see which step failed
- **Visibility**: GitHub Actions tab shows flow

### **✅ Flexibility**
- **Can add steps**: Deploy workflow can be extended
- **Can add conditions**: Only deploy on specific branches
- **Can add notifications**: Slack, email, etc.

---

## 🐛 Troubleshooting

### **Deploy not triggering?**
1. **Check CI name**: Must be exactly "CI"
2. **Check conclusion**: Must be "success"
3. **Check branch**: Must be "master"

### **Auto-merge not working?**
1. **Check PR state**: Must be "clean" and "mergeable"
2. **Check permissions**: GITHUB_TOKEN needs write access
3. **Check conflicts**: No merge conflicts allowed

### **Render not deploying?**
1. **Check webhook**: Render webhook must be active
2. **Check branch**: Must be set to "master"
3. **Check auto-deploy**: Must be enabled

---

## 🔄 Migration from Push-based

### **Before:**
```yaml
# Didn't work due to GITHUB_TOKEN limitation
on:
  push:
    branches: [master]
```

### **After:**
```yaml
# Works reliably with workflow_run
on:
  workflow_run:
    workflows: ["CI"]
    types: [completed]
```

---

## 📚 References

- [GitHub Actions: `workflow_run`](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
- [GitHub: GITHUB_TOKEN limitations](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
- [Render: GitHub Integration](https://render.com/docs/deploy-github)
