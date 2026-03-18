# Personal Access Token (PAT) Setup for Auto-Merge

## 🎯 Why We Need PAT

**Problem:** GitHub Actions using `GITHUB_TOKEN` cannot trigger other workflows (like push workflows).

**Solution:** Use a Personal Access Token (PAT) with proper permissions.

---

## 🔧 Step-by-Step Setup

### **1. Create Personal Access Token**

1. **Go to GitHub Settings:**
   ```
   https://github.com/settings/tokens
   ```

2. **Click "Generate new token" → "Generate new token (classic)"

3. **Configure token:**
   - **Name:** `Auto-merge Trading App`
   - **Expiration:** Choose appropriate period (90 days recommended)
   - **Scopes (Permissions):**
     ```
     ✅ repo          # Full control of repositories
     ✅ workflow     # Update GitHub Action workflows
     ```

4. **Click "Generate token"**
5. **⚠️ IMPORTANT:** Copy the token immediately (you won't see it again!)

---

### **2. Add PAT to GitHub Secrets**

1. **Go to your repository:**
   ```
   https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Create secret:**
   - **Name:** `PAT_TOKEN`
   - **Secret:** [Paste the token you copied]

4. **Click "Add secret"

---

## 🚀 How It Works

### **Before (GITHUB_TOKEN):**
```yaml
# ❌ Doesn't trigger push workflows
- name: Auto-merge PR
  uses: actions/github-script@v8
  with:
    github-token: ${{ secrets.GITHUB_TOKEN }}
```

### **After (PAT_TOKEN):**
```yaml
# ✅ Triggers push workflows
- name: Auto-merge PR
  uses: actions/github-script@v8
  with:
    github-token: ${{ secrets.PAT_TOKEN }}
```

---

## 🔄 Flow with PAT

```
Pull Request → CI Tests → Auto-merge (PAT) → Real Push → Deploy Workflow → Render
```

1. **PR created** → CI workflow runs
2. **Tests pass** → Auto-merge with PAT
3. **PAT merge** → Creates real push event
4. **Push detected** → Deploy workflow triggers
5. **Render detects** → Auto-deployment starts

---

## ⚠️ Security Considerations

### **✅ Best Practices:**

1. **Minimum permissions:** Only `repo` and `workflow`
2. **Regular rotation:** Set expiration (90 days max)
3. **Repository-specific:** Don't use organization-wide PAT
4. **Monitor usage:** Check token usage in GitHub settings

### **❌ What to Avoid:**

1. **Don't commit PAT to code** (use secrets)
2. **Don't share PAT** with team members unnecessarily
3. **Don't use excessive permissions** (only what's needed)
4. **Don't forget to rotate** expired tokens

---

## 🐛 Troubleshooting

### **Auto-merge not working?**

1. **Check PAT exists:**
   ```bash
   # In GitHub Actions logs, look for:
   # "PAT_TOKEN" should be masked (***)
   ```

2. **Check PAT permissions:**
   - Go to GitHub Settings → Personal access tokens
   - Verify token has `repo` and `workflow` scopes

3. **Check PAT expiration:**
   - Token might have expired
   - Generate new token if needed

### **Push workflow not triggering?**

1. **Check merge method:**
   ```yaml
   # Must be 'merge' (not 'squash' or 'rebase')
   merge_method: 'merge'
   ```

2. **Check branch name:**
   - Must be exactly `master` (not `main`)

3. **Check PAT permissions:**
   - PAT must have `workflow` scope

---

## 🔄 Token Rotation

### **Every 90 days:**

1. **Generate new PAT** (follow steps above)
2. **Update repository secret:**
   - Go to repository settings → secrets
   - Delete old `PAT_TOKEN`
   - Add new `PAT_TOKEN`

3. **Test the flow:**
   - Create test PR
   - Verify auto-merge works
   - Verify deploy triggers

---

## 📚 References

- [GitHub: Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub: Permissions for personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/permissions-for-personal-access-tokens)
- [Render: GitHub Integration](https://render.com/docs/deploy-github)

---

## 🎯 Quick Checklist

- [ ] PAT created with `repo` and `workflow` permissions
- [ ] PAT added as `PAT_TOKEN` secret
- [ ] PAT expiration set (≤ 90 days)
- [ ] Auto-merge uses `PAT_TOKEN` (not `GITHUB_TOKEN`)
- [ ] Deploy workflow triggers on `push: [master]`
- [ ] Test PR created and merged successfully
- [ ] Render deployment triggered automatically
