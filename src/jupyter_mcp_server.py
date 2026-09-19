"""
Jupyter Notebook MCP Server built on official MCPServer (MCP 2.x compliant).
Standalone implementation using nbformat and nbclient, completely independent
of legacy/broken mcp_server_jupyter packages.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import nbformat
from nbclient import NotebookClient
from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    "jupyter",
    instructions="Jupyter notebook management MCP server for creating, reading, editing, and executing notebooks."
)


class NotebookHelper:
    def __init__(self, notebook_path: str):
        self.path = Path(notebook_path).resolve()
        if not self.path.exists():
            raise FileNotFoundError(f"Notebook not found at: {self.path}")
        with open(self.path, "r", encoding="utf-8") as f:
            self.nb = nbformat.read(f, as_version=4)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            nbformat.write(self.nb, f)

    def get_cell(self, cell_id: str):
        for cell in self.nb.cells:
            if cell.get("id") == cell_id:
                return cell
        raise ValueError(f"No cell found with ID: {cell_id}")


@mcp.tool()
def read_notebook(notebook_path: str, with_outputs: bool = True) -> str:
    """
    Read the contents and structure of a Jupyter notebook.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        with_outputs: Whether to include cell execution outputs.
    """
    try:
        helper = NotebookHelper(notebook_path)
        lines = [f"# Notebook: {helper.path.name} ({len(helper.nb.cells)} cells)\n"]
        for idx, cell in enumerate(helper.nb.cells):
            cid = cell.get("id", f"cell-{idx}")
            ctype = cell.get("cell_type", "unknown")
            lines.append(f"--- [Cell {idx}] ID: {cid} | Type: {ctype} ---")
            lines.append(cell.get("source", ""))
            
            if with_outputs and ctype == "code":
                outputs = cell.get("outputs", [])
                if outputs:
                    lines.append("  [Outputs]:")
                    for out in outputs:
                        out_type = out.get("output_type")
                        if out_type == "stream":
                            lines.append(f"    {out.get('text', '').strip()}")
                        elif out_type in ("execute_result", "display_data"):
                            data = out.get("data", {})
                            if "text/plain" in data:
                                lines.append(f"    {data['text/plain']}")
                            elif "image/png" in data:
                                lines.append("    [Image Display: PNG]")
                        elif out_type == "error":
                            ename = out.get("ename", "Error")
                            evalue = out.get("evalue", "")
                            lines.append(f"    [Error] {ename}: {evalue}")
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading notebook: {str(e)}"


@mcp.tool()
def read_output_of_cell(notebook_path: str, cell_id: str) -> str:
    """
    Read the execution output of a specific code cell.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        cell_id: Unique ID of the target cell.
    """
    try:
        helper = NotebookHelper(notebook_path)
        cell = helper.get_cell(cell_id)
        if cell.get("cell_type") != "code":
            return f"Cell '{cell_id}' is a {cell.get('cell_type')} cell, not a code cell."
        outputs = cell.get("outputs", [])
        if not outputs:
            return f"Cell '{cell_id}' has no outputs recorded."
        
        lines = []
        for out in outputs:
            out_type = out.get("output_type")
            if out_type == "stream":
                lines.append(out.get("text", ""))
            elif out_type in ("execute_result", "display_data"):
                data = out.get("data", {})
                if "text/plain" in data:
                    lines.append(data["text/plain"])
            elif out_type == "error":
                lines.append(f"Error {out.get('ename')}: {out.get('evalue')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading cell output: {str(e)}"


@mcp.tool()
def add_cell(notebook_path: str, cell_type: str = "code", source: str = "", position: int = -1) -> str:
    """
    Add a new cell to a notebook at the specified position.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        cell_type: Type of cell ('code', 'markdown', or 'raw').
        source: Content of the cell.
        position: Position index (-1 to append at end).
    """
    try:
        helper = NotebookHelper(notebook_path)
        if cell_type == "code":
            new_cell = nbformat.v4.new_code_cell(source=source)
        elif cell_type == "markdown":
            new_cell = nbformat.v4.new_markdown_cell(source=source)
        elif cell_type == "raw":
            new_cell = nbformat.v4.new_raw_cell(source=source)
        else:
            return f"Error: Unsupported cell type '{cell_type}'."

        if position == -1 or position >= len(helper.nb.cells):
            helper.nb.cells.append(new_cell)
            new_idx = len(helper.nb.cells) - 1
        else:
            helper.nb.cells.insert(position, new_cell)
            new_idx = position
        
        helper.save()
        return f"Cell added successfully at index {new_idx} with ID: {new_cell.get('id')}"
    except Exception as e:
        return f"Error adding cell: {str(e)}"


@mcp.tool()
def edit_cell(notebook_path: str, cell_id: str, source: str) -> str:
    """
    Edit the source content of an existing cell in the notebook.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        cell_id: Unique ID of the cell to update.
        source: New code or markdown content.
    """
    try:
        helper = NotebookHelper(notebook_path)
        cell = helper.get_cell(cell_id)
        cell["source"] = source
        helper.save()
        return f"Cell '{cell_id}' successfully updated."
    except Exception as e:
        return f"Error editing cell: {str(e)}"


@mcp.tool()
def delete_cell(notebook_path: str, cell_id: str) -> str:
    """
    Delete a cell from the notebook by its ID.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        cell_id: Unique ID of the cell to delete.
    """
    try:
        helper = NotebookHelper(notebook_path)
        initial_len = len(helper.nb.cells)
        helper.nb.cells = [c for c in helper.nb.cells if c.get("id") != cell_id]
        if len(helper.nb.cells) == initial_len:
            return f"Error: No cell found with ID '{cell_id}' to delete."
        helper.save()
        return f"Cell '{cell_id}' successfully deleted."
    except Exception as e:
        return f"Error deleting cell: {str(e)}"


@mcp.tool()
def execute_cell(notebook_path: str, cell_id: str) -> str:
    """
    Execute a single cell in the notebook using the active Python kernel.
    
    Args:
        notebook_path: Path to the .ipynb notebook file.
        cell_id: ID of the cell to execute.
    """
    try:
        helper = NotebookHelper(notebook_path)
        cell = helper.get_cell(cell_id)
        cell_idx = helper.nb.cells.index(cell)
        
        client = NotebookClient(helper.nb, timeout=600)
        with client.setup_kernel():
            client.execute_cell(cell, cell_idx)
        helper.save()
        
        outputs = cell.get("outputs", [])
        if not outputs:
            return f"Cell '{cell_id}' executed successfully (no stdout)."
        
        lines = []
        for out in outputs:
            if out.get("output_type") == "stream":
                lines.append(out.get("text", ""))
            elif "data" in out and "text/plain" in out["data"]:
                lines.append(out["data"]["text/plain"])
            elif out.get("output_type") == "error":
                lines.append(f"Error {out.get('ename')}: {out.get('evalue')}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error executing cell: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
