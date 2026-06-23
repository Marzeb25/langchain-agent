import json
import os
from datetime import datetime
from pathlib import Path
import asyncio
from typing import Dict, List, Optional, Tuple
import httpx
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from dotenv import load_dotenv

load_dotenv()

class MCPToolManager:
    """Manages MCP Tools for GitHub and Filesystem access"""
    
    def __init__(self, mcp_config_path: str = "mcp_config.json"):
        self.config = self._load_config(mcp_config_path)
        self.github_enabled = self._check_tool_availability("github")
        self.filesystem_enabled = self._check_tool_availability("filesystem")
        self.github_token = os.environ.get("GITHUB_TOKEN", "")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load MCP configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {"mcpServers": {}}
    
    def _check_tool_availability(self, tool_name: str) -> bool:
        """Check if a tool is properly configured"""
        return tool_name in self.config.get("mcpServers", {})
    
    async def fetch_pr_details(self, owner: str, repo: str, pr_number: str) -> Dict:
        """Fetch PR details from GitHub API"""
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
                headers = {
                    "Accept": "application/vnd.github.v3+json"
                }
                
                if self.github_token:
                    headers["Authorization"] = f"token {self.github_token}"
                
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                pr_data = response.json()
                
                # Extract relevant PR information
                return {
                    "pr_number": pr_data.get("number"),
                    "title": pr_data.get("title"),
                    "description": pr_data.get("body", ""),
                    "files_changed": pr_data.get("changed_files", 0),
                    "additions": pr_data.get("additions", 0),
                    "deletions": pr_data.get("deletions", 0),
                    "author": pr_data.get("user", {}).get("login"),
                    "url": pr_data.get("html_url"),
                    "state": pr_data.get("state")
                }
        except Exception as e:
            raise Exception(f"Failed to fetch PR details from GitHub: {str(e)}")
    
    async def read_file(self, file_path: str) -> str:
        """Read file using filesystem MCP"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return ""
    
    async def write_file(self, file_path: str, content: str) -> bool:
        """Write file using filesystem MCP"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error writing file: {e}")
            return False


class TechnoDocGenerator:
    """Generates Technical Documentation for PR changes"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, mcp_manager: MCPToolManager):
        self.llm = llm
        self.mcp_manager = mcp_manager
        self.docs_dir = Path("docs/techno")
        self.docs_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, pr_info: Dict, existing_doc: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate technical documentation
        Returns: (generated_doc, status_message)
        """
        template = await self.mcp_manager.read_file("templates/techno_doc_template.md")
        
        if existing_doc:
            prompt = f"""You are a technical documentation expert. 
A PR has been submitted with changes. Based on the existing documentation and the PR details:

PR Details:
{json.dumps(pr_info, indent=2)}

Existing Documentation:
{existing_doc}

Please update the technical documentation to reflect the new changes while maintaining the structure. 
Compare what changed and update only the relevant sections."""
        else:
            prompt = f"""You are a technical documentation expert.
A new PR has been submitted. Based on the PR details and this template:

{template}

PR Details:
{json.dumps(pr_info, indent=2)}

Please generate a comprehensive technical documentation following the template structure."""
        
        messages = [
            SystemMessage(content="You are a technical documentation expert who creates clear, comprehensive technical documentation."),
            HumanMessage(content=prompt)
        ]
        
        response = ""
        async for chunk in self.llm.astream(messages):
            response += chunk.content if isinstance(chunk.content, str) else ""
        
        # Save the document
        doc_name = f"techno_doc_{pr_info.get('pr_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        doc_path = self.docs_dir / doc_name
        
        await self.mcp_manager.write_file(str(doc_path), response)
        
        return response, f"✓ Technical documentation generated: {doc_name}"


class ThreatModelingReportGenerator:
    """Generates OWASP-compliant Threat Modeling Report"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, mcp_manager: MCPToolManager):
        self.llm = llm
        self.mcp_manager = mcp_manager
        self.reports_dir = Path("reports/threat_modeling")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, pr_info: Dict, existing_report: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate OWASP Threat Modeling Report
        Returns: (generated_report, status_message)
        """
        owasp_requirements = await self.mcp_manager.read_file("templates/owasp_requirements.md")
        
        if existing_report:
            prompt = f"""You are a security expert specializing in OWASP threat modeling.
A PR has been submitted with changes. Analyze if any previously identified threats have been resolved:

PR Details:
{json.dumps(pr_info, indent=2)}

Existing Threat Report:
{existing_report}

OWASP Guidelines:
{owasp_requirements}

Please:
1. Review the PR changes
2. Update the threat status for any resolved issues (mark as 'Resolved')
3. Identify any new threats introduced
4. Update the report with these changes"""
        else:
            prompt = f"""You are a security expert specializing in OWASP threat modeling.
Analyze this PR for potential security threats and create a comprehensive threat modeling report:

PR Details:
{json.dumps(pr_info, indent=2)}

OWASP Guidelines to follow:
{owasp_requirements}

Please create a detailed threat modeling report following the OWASP structure provided."""
        
        messages = [
            SystemMessage(content="You are a security expert specializing in OWASP threat modeling and vulnerability assessment."),
            HumanMessage(content=prompt)
        ]
        
        response = ""
        async for chunk in self.llm.astream(messages):
            response += chunk.content if isinstance(chunk.content, str) else ""
        
        # Save the report
        report_name = f"threat_model_{pr_info.get('pr_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        report_path = self.reports_dir / report_name
        
        await self.mcp_manager.write_file(str(report_path), response)
        
        return response, f"✓ Threat modeling report generated: {report_name}"


class MindMapGenerator:
    """Generates Mind Map of PR changes and their impact on existing flows"""
    
    def __init__(self, llm: ChatGoogleGenerativeAI, mcp_manager: MCPToolManager):
        self.llm = llm
        self.mcp_manager = mcp_manager
        self.mindmaps_dir = Path("docs/mindmaps")
        self.mindmaps_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate(self, pr_info: Dict, existing_mindmap: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate Mind Map visualization in Markdown
        Returns: (generated_mindmap, status_message)
        """
        if existing_mindmap:
            prompt = f"""You are an architect specializing in system design.
A PR has been submitted with changes. Create an updated mind map showing how the new changes integrate:

PR Details:
{json.dumps(pr_info, indent=2)}

Existing Architecture Mind Map:
{existing_mindmap}

Please:
1. Analyze how the PR changes affect the existing architecture
2. Create an updated mind map using Markdown format
3. Highlight new components and modified flows
4. Show the integration points with existing systems"""
        else:
            prompt = f"""You are an architect specializing in system design.
Create a comprehensive mind map showing a PR's changes and how they affect the system's existing flows:

PR Details:
{json.dumps(pr_info, indent=2)}

Please create a detailed mind map in Markdown format that shows:
1. The main changes introduced by the PR
2. Affected components
3. Impact on existing workflows
4. Integration points
5. Dependencies

Use this format:
- Central Topic
  - Branch 1
    - Sub-item
  - Branch 2
    - Sub-item"""
        
        messages = [
            SystemMessage(content="You are an architect who creates clear mind maps showing system changes and their impact."),
            HumanMessage(content=prompt)
        ]
        
        response = ""
        async for chunk in self.llm.astream(messages):
            response += chunk.content if isinstance(chunk.content, str) else ""
        
        # Save the mind map
        mm_name = f"mindmap_{pr_info.get('pr_number', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        mm_path = self.mindmaps_dir / mm_name
        
        await self.mcp_manager.write_file(str(mm_path), response)
        
        return response, f"✓ Mind map generated: {mm_name}"


class PRAnalysisEngine:
    """Main engine for parallel PR analysis"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Please set GOOGLE_API_KEY or GEMINI_API_KEY in your .env file")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=self.api_key,
            include_thoughts=True
        )
        self.mcp_manager = MCPToolManager()
        self.techno_gen = TechnoDocGenerator(self.llm, self.mcp_manager)
        self.threat_gen = ThreatModelingReportGenerator(self.llm, self.mcp_manager)
        self.mindmap_gen = MindMapGenerator(self.llm, self.mcp_manager)
    
    async def check_existing_files(self, pr_number: str) -> Dict[str, Optional[str]]:
        """Check if analysis files already exist for this PR"""
        existing = {
            "techno_doc": None,
            "threat_report": None,
            "mindmap": None
        }
        
        # Search for existing files matching PR number
        techno_dir = Path("docs/techno")
        reports_dir = Path("reports/threat_modeling")
        mindmaps_dir = Path("docs/mindmaps")
        
        for dir_path, key in [(techno_dir, "techno_doc"), 
                               (reports_dir, "threat_report"), 
                               (mindmaps_dir, "mindmap")]:
            if dir_path.exists():
                for file in dir_path.glob(f"*{pr_number}*"):
                    content = await self.mcp_manager.read_file(str(file))
                    if content:
                        existing[key] = content
        
        return existing
    
    async def analyze_pr(self, pr_info: Dict, human_approval_callback=None) -> Dict:
        """
        Perform parallel analysis of PR
        Returns results from all three analysis tasks
        """
        # Check for existing analysis
        existing_files = await self.check_existing_files(pr_info.get("pr_number", "unknown"))
        
        # Run parallel analysis tasks
        tasks = [
            self.techno_gen.generate(pr_info, existing_files["techno_doc"]),
            self.threat_gen.generate(pr_info, existing_files["threat_report"]),
            self.mindmap_gen.generate(pr_info, existing_files["mindmap"])
        ]
        
        results = await asyncio.gather(*tasks)
        
        return {
            "pr_number": pr_info.get("pr_number"),
            "timestamp": datetime.now().isoformat(),
            "techno_doc": {
                "content": results[0][0],
                "status": results[0][1],
                "is_update": existing_files["techno_doc"] is not None
            },
            "threat_report": {
                "content": results[1][0],
                "status": results[1][1],
                "is_update": existing_files["threat_report"] is not None
            },
            "mindmap": {
                "content": results[2][0],
                "status": results[2][1],
                "is_update": existing_files["mindmap"] is not None
            }
        }
