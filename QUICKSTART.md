# Quick Start Guide - PR Analysis System

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
Create `.env` file in the project root:
```env
GOOGLE_API_KEY=your_actual_gemini_api_key_here
```

Get your API key from: https://ai.google.dev/

### Step 3: Configure MCP (Optional but Recommended)
Edit `mcp_config.json`:
```json
{
  "mcpServers": {
    "github": {
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_OWNER": "your_github_username",
        "GITHUB_REPO": "your_repo_name"
      }
    },
    "filesystem": {
      "env": {
        "ALLOWED_DIRECTORIES": "/full/path/to/docs,/full/path/to/reports"
      }
    }
  }
}
```

Get GitHub token from: https://github.com/settings/tokens

### Step 4: Run the Server
```bash
python app.py
```

Server will start at: `http://localhost:8000`

### Step 5: Access the UI
- Open browser to `http://localhost:8000`
- Two tabs available:
  - **💬 Chat**: Chat with AI assistant
  - **📋 PR Analysis**: Analyze pull requests

---

## Using PR Analysis

### Input PR Information
1. Click **PR Analysis** tab
2. Fill in:
   - **PR Number**: e.g., `123`
   - **PR Title**: e.g., `Add user authentication`
   - **PR Description**: Detailed description of changes
   - **Files Changed**: Comma-separated file list
   - **Additions/Deletions**: Line counts (optional)

### View Results
Three analyses will run in parallel:
1. **📄 Technical Documentation**
   - Architecture overview
   - Changes made
   - Impact analysis
   - Deployment notes

2. **🛡️ Threat Modeling Report**
   - OWASP-compliant security analysis
   - Threat identification
   - Risk assessment
   - Mitigation recommendations

3. **🗺️ Mind Map**
   - Visual representation of changes
   - Affected components
   - Integration points
   - System flows

### Approve or Reject
After analysis:
- Review each section (click to expand)
- Check items you approve
- Add optional notes
- Click **✓ Approve** or **✗ Reject**

---

## Output Files

Results are automatically saved to:
- **Technical Docs**: `docs/techno/techno_doc_{PR#}_{timestamp}.md`
- **Threat Reports**: `reports/threat_modeling/threat_model_{PR#}_{timestamp}.md`
- **Mind Maps**: `docs/mindmaps/mindmap_{PR#}_{timestamp}.md`

---

## Troubleshooting

### "API Key Error"
- Verify `.env` file exists in project root
- Check `GOOGLE_API_KEY` is set correctly
- Restart server after updating `.env`

### "Connection refused"
- Ensure `python app.py` is running
- Check port 8000 is not in use: `lsof -i :8000`
- Try different port: Edit `app.py`, change port from 8000

### "MCP Tool not available"
- MCP tools are optional; system works without them
- To enable, configure `mcp_config.json` properly
- Check GitHub token has `repo` permissions

### "Files not saving"
- Ensure `docs/`, `reports/` directories exist
- Check write permissions: `chmod 755 docs reports`
- Create directories if missing:
  ```bash
  mkdir -p docs/techno reports/threat_modeling docs/mindmaps
  ```

---

## Example PR Analysis Request

```
PR Number: 42
PR Title: Implement OAuth2 Authentication
PR Description: Add OAuth2 provider integration with Google and GitHub
Files Changed: 
  - src/auth/oauth.js
  - src/auth/config.ts
  - src/routes/login.js
  - tests/auth.test.js
Additions: 350
Deletions: 45
```

---

## Full Documentation

See `PR_ANALYSIS_README.md` for:
- Complete API reference
- Customization options
- Advanced features
- Detailed troubleshooting

---

## Next Steps

1. **Test Chat**: Try basic conversation first
2. **Test PR Analysis**: Submit a sample PR for analysis
3. **Review Outputs**: Check generated docs in `docs/` and `reports/`
4. **Approve Changes**: Practice the approval workflow
5. **Customize Templates**: Edit `templates/` files for your needs

---

## Support

For issues:
1. Check console for error messages
2. Review `PR_ANALYSIS_README.md` troubleshooting section
3. Verify environment setup in Step 2
4. Check file permissions in Step 3

Happy analyzing! 🚀
