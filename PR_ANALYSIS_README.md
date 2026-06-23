# PR Analysis System - Setup & Usage Guide

## Overview

This system provides comprehensive PR analysis using Google Gemini AI and LangChain with MCP (Model Context Protocol) tools for GitHub and filesystem integration.

### Features

1. **Technical Documentation Generation** (`📄`)
   - Auto-generates technical documentation for PR changes
   - Updates existing documentation when PR changes existing features
   - Follows a structured template covering architecture, changes, dependencies, and deployment notes

2. **OWASP Threat Modeling Report** (`🛡️`)
   - Performs security threat analysis following OWASP Top 10 guidelines
   - Creates comprehensive threat reports with risk assessment
   - Tracks threat status and updates when issues are resolved in new PRs
   - Includes mitigation roadmap and compliance requirements

3. **Mind Map Generation** (`🗺️`)
   - Creates visual mind maps showing PR changes and their system impact
   - Shows integration points and affected components
   - Updates when new changes affect existing architecture

## Project Structure

```
langchain-agent/
├── app.py                           # Main FastAPI application
├── pr_analyzer.py                   # PR analysis engine with parallel processing
├── index.html                       # UI with Chat and PR Analysis tabs
├── mcp_config.json                  # MCP configuration template
├── templates/
│   ├── techno_doc_template.md       # Technical documentation template
│   └── owasp_requirements.md        # OWASP threat modeling guidelines
├── docs/
│   ├── techno/                      # Generated technical documentation
│   └── mindmaps/                    # Generated mind maps
└── reports/
    └── threat_modeling/             # Generated threat modeling reports
```

## Setup Instructions

### 1. Environment Setup

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
# or use:
# GEMINI_API_KEY=your_gemini_api_key_here
```

### 2. Install Dependencies

```bash
pip install fastapi uvicorn langchain langchain-google-genai python-dotenv
```

### 3. Configure MCP Servers

Edit `mcp_config.json` with your GitHub and filesystem settings:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "your_github_token",
        "GITHUB_OWNER": "your_owner",
        "GITHUB_REPO": "your_repo"
      }
    },
    "filesystem": {
      "command": "node",
      "args": ["mcp_server_filesystem.js"],
      "env": {
        "ALLOWED_DIRECTORIES": "/path/to/docs,/path/to/reports"
      }
    }
  }
}
```

### 4. Start the Server

```bash
python app.py
```

The server will start at `http://localhost:8000`

## Usage

### Chat Interface

- Use the **💬 Chat** tab for general conversations
- Messages are streamed with thought processes displayed
- Full chat history is maintained

### PR Analysis

1. Click the **📋 PR Analysis** tab
2. Fill in PR details:
   - **PR Number**: Unique identifier (e.g., 123)
   - **PR Title**: Brief description of changes
   - **PR Description**: Detailed explanation of changes
   - **Files Changed**: Comma-separated list of modified files
   - **Additions/Deletions**: Line counts (optional)

3. Click **🚀 Analyze PR** to start parallel analysis

4. Review the generated outputs:
   - **Technical Documentation**: Overview of changes and impact
   - **Threat Modeling Report**: Security analysis and recommendations
   - **Mind Map**: Visual representation of changes and affected flows

### Human Intervention

After analysis completes, you can:

- **Approve**: Select items to approve and confirm
- **Reject**: Provide feedback for regeneration
- **Add Notes**: Include additional context or requirements

## File Comparison & Updates

When analyzing a PR with existing analysis files:

- **Techno Doc**: Automatically compares and updates with new changes
- **Threat Report**: Updates threat status (marks resolved issues as "Resolved")
- **Mind Map**: Integrates new components while maintaining existing structure

## API Endpoints

### Chat Endpoint
```
POST /chat
Content-Type: application/json
Body: { "message": "your message" }
Response: Server-Sent Events (streaming)
```

### PR Analysis Endpoint
```
POST /analyze-pr
Content-Type: application/json
Body: {
  "pr_number": "123",
  "title": "PR Title",
  "description": "PR Description",
  "files_changed": ["file1.js", "file2.js"],
  "additions": 100,
  "deletions": 50
}
Response: Server-Sent Events (streaming) with analysis results
```

### Approval Endpoint
```
POST /approve-changes
Content-Type: application/json
Body: {
  "pr_number": "123",
  "approved_items": ["techno_doc", "threat_report", "mindmap"],
  "notes": "Approved with comments"
}
Response: { "status": "approved", ... }
```

### Rejection Endpoint
```
POST /reject-changes
Content-Type: application/json
Body: {
  "pr_number": "123",
  "reason": "Needs revision for security"
}
Response: { "status": "rejected", ... }
```

## Parallel Processing

The system uses Python's `asyncio` for parallel processing of:
1. Technical Documentation Generation
2. Threat Modeling Report Generation
3. Mind Map Generation

All three tasks run concurrently and results are streamed back to the UI.

## Output Locations

- **Technical Docs**: `docs/techno/techno_doc_{pr_number}_{timestamp}.md`
- **Threat Reports**: `reports/threat_modeling/threat_model_{pr_number}_{timestamp}.md`
- **Mind Maps**: `docs/mindmaps/mindmap_{pr_number}_{timestamp}.md`

## Customization

### Modify Document Templates

Edit these files to customize output format:
- `templates/techno_doc_template.md`
- `templates/owasp_requirements.md`

### Adjust AI Behavior

Modify the system prompts in `pr_analyzer.py` classes:
- `TechnoDocGenerator.__init__()`
- `ThreatModelingReportGenerator.__init__()`
- `MindMapGenerator.__init__()`

### Configure Analysis Depth

Adjust the LLM model in `app.py`:
```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Change to other models if needed
    api_key=api_key,
    include_thoughts=True
)
```

## Troubleshooting

### API Key Issues
Ensure your `.env` file has the correct Google API key:
```bash
echo $GOOGLE_API_KEY  # Should show your key
```

### MCP Connection Issues
Verify MCP configuration in `mcp_config.json` and check GitHub token permissions:
- `repo` scope for private repositories
- `public_repo` scope for public repositories

### File Write Errors
Ensure directories exist and have write permissions:
```bash
mkdir -p docs/techno reports/threat_modeling docs/mindmaps
chmod 755 docs reports
```

## Future Enhancements

- [ ] GitHub webhook integration for automatic PR analysis
- [ ] Database storage for analysis history
- [ ] Custom metrics and KPIs
- [ ] Multi-language support
- [ ] Integration with CI/CD pipelines
- [ ] Comparison reports between PRs
- [ ] Custom threat categories

## Support

For issues or questions, refer to:
- LangChain Documentation: https://python.langchain.com/
- Google Generative AI: https://ai.google.dev/
- MCP Protocol: https://modelcontextprotocol.io/
