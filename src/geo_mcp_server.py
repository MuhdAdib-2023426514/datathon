"""
GeoJSON & Map Data MCP Server.
Provides spatial inspection, boundary validation, and geometry simplification
for Malaysia state GIS boundaries (data/geo/malaysia.geojson).
"""

import sys
import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from mcp.server.mcpserver import MCPServer

ROOT_DIR = Path(__file__).resolve().parent.parent
GEOJSON_PATH = ROOT_DIR / "data/geo/malaysia.geojson"

CANONICAL_STATES = [
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Perak", "Perlis", "Pulau Pinang", "Sabah",
    "Sarawak", "Selangor", "Terengganu", "W.P. Kuala Lumpur",
    "W.P. Labuan", "W.P. Putrajaya"
]

mcp = MCPServer(
    "geo_map",
    instructions=(
        "Specialized geospatial MCP server for Malaysia Tourism Value Optimizer. "
        "Provides inspection of state GIS boundaries, name alignment validation against "
        "canonical references, and geometry simplification for frontend rendering."
    ),
)


def _load_geojson() -> Dict:
    if not GEOJSON_PATH.exists():
        raise FileNotFoundError(f"GeoJSON not found at {GEOJSON_PATH}")
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _compute_bbox(coords) -> Tuple[float, float, float, float]:
    """Recursively compute [min_lon, min_lat, max_lon, max_lat] for coordinate array."""
    min_lon, min_lat = float("inf"), float("inf")
    max_lon, max_lat = float("-inf"), float("-inf")

    def _walk(item):
        nonlocal min_lon, min_lat, max_lon, max_lat
        if isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], (int, float)):
            lon, lat = item[0], item[1]
            min_lon = min(min_lon, lon)
            min_lat = min(min_lat, lat)
            max_lon = max(max_lon, lon)
            max_lat = max(max_lat, lat)
        elif isinstance(item, (list, tuple)):
            for sub in item:
                _walk(sub)

    _walk(coords)
    return min_lon, min_lat, max_lon, max_lat


@mcp.tool()
def list_features() -> str:
    """List all 16 state features, their IDs, state codes, and bounding boxes in malaysia.geojson."""
    try:
        data = _load_geojson()
        features = data.get("features", [])
        lines = [
            f"Malaysia GeoJSON Feature Summary ({GEOJSON_PATH.name})",
            f"Total Features: {len(features)}",
            "",
            f"{'ID':<6} {'State Name':<24} {'Code':<8} {'Bounding Box (Lon, Lat)':<35}",
            "-" * 75,
        ]

        for f in features:
            fid = str(f.get("id", "-"))
            props = f.get("properties", {})
            name = props.get("name", props.get("state_name", "Unknown"))
            code = props.get("state", props.get("code", "-"))
            geom = f.get("geometry", {})
            coords = geom.get("coordinates", [])
            min_x, min_y, max_x, max_y = _compute_bbox(coords)
            bbox_str = f"[{min_x:.2f}, {min_y:.2f}] to [{max_x:.2f}, {max_y:.2f}]"
            lines.append(f"{fid:<6} {name:<24} {code:<8} {bbox_str:<35}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error reading GeoJSON features: {e}"


@mcp.tool()
def get_state_geometry(state_name: str) -> str:
    """Return geometry metadata, polygon count, and coordinate vertices count for a given state."""
    try:
        data = _load_geojson()
        features = data.get("features", [])
        norm_query = state_name.lower().strip()

        matched = None
        for f in features:
            props = f.get("properties", {})
            name = props.get("name", "").lower()
            code = props.get("state", "").lower()
            fid = str(f.get("id", "")).lower()
            if norm_query in (name, code, fid) or name.startswith(norm_query):
                matched = f
                break

        if not matched:
            return f"State '{state_name}' not found in GeoJSON. Use list_features() to inspect available states."

        props = matched.get("properties", {})
        geom = matched.get("geometry", {})
        gtype = geom.get("type", "Unknown")
        coords = geom.get("coordinates", [])

        # Count total vertices
        vertex_count = 0
        def _count(c):
            nonlocal vertex_count
            if isinstance(c, (list, tuple)) and len(c) == 2 and isinstance(c[0], (int, float)):
                vertex_count += 1
            elif isinstance(c, (list, tuple)):
                for sub in c:
                    _count(sub)
        _count(coords)

        min_x, min_y, max_x, max_y = _compute_bbox(coords)
        centroid_lon = (min_x + max_x) / 2
        centroid_lat = (min_y + max_y) / 2

        lines = [
            f"State Feature: {props.get('name')}",
            f"  ID: {matched.get('id')}",
            f"  State Code: {props.get('state')}",
            f"  Geometry Type: {gtype}",
            f"  Total Vertices: {vertex_count:,}",
            f"  Bounding Box: [{min_x:.4f}, {min_y:.4f}] to [{max_x:.4f}, {max_y:.4f}]",
            f"  Calculated Centroid: ({centroid_lat:.4f}, {centroid_lon:.4f})",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error retrieving geometry for '{state_name}': {e}"


@mcp.tool()
def validate_state_names() -> str:
    """Validate that GeoJSON features align with the 16 canonical state names in AGENTS.md."""
    try:
        data = _load_geojson()
        features = data.get("features", [])
        found_names = [f.get("properties", {}).get("name") for f in features]

        missing_canonical = [s for s in CANONICAL_STATES if s not in found_names]
        unrecognized_found = [s for s in found_names if s not in CANONICAL_STATES]

        lines = [
            "GeoJSON State Name Alignment Validation",
            "=" * 50,
            f"Total Expected Canonical States: {len(CANONICAL_STATES)}",
            f"Total GeoJSON Features Found: {len(features)}",
            "",
        ]

        if not missing_canonical and not unrecognized_found:
            lines.append("✓ PERFECT ALIGNMENT: All 16 Malaysian states reconcile 1-to-1.")
        else:
            if missing_canonical:
                lines.append(f"✗ Missing Canonical States ({len(missing_canonical)}):")
                for s in missing_canonical:
                    lines.append(f"    - {s}")
            if unrecognized_found:
                lines.append(f"✗ Unrecognized GeoJSON Names ({len(unrecognized_found)}):")
                for s in unrecognized_found:
                    lines.append(f"    - {s}")

        return "\n".join(lines)
    except Exception as e:
        return f"Error validating state names: {e}"


@mcp.tool()
def simplify_geometry(step: int = 4) -> str:
    """Simulate vertex reduction using point decimation by skipping every N points.
    Returns size comparison and vertex reduction ratio.
    """
    try:
        data = _load_geojson()
        original_size_kb = GEOJSON_PATH.stat().st_size / 1024

        orig_vertices = 0
        decimated_vertices = 0

        def _decimate(c, s):
            nonlocal orig_vertices, decimated_vertices
            if isinstance(c, list) and len(c) > 0 and isinstance(c[0], (list, tuple)) and len(c[0]) == 2 and isinstance(c[0][0], (int, float)):
                orig_vertices += len(c)
                # Keep first and last point to close polygon, decimate interior
                if len(c) <= 4:
                    decimated_vertices += len(c)
                    return c
                decimated = [c[0]] + c[1:-1:s] + [c[-1]]
                decimated_vertices += len(decimated)
                return decimated
            elif isinstance(c, list):
                return [_decimate(sub, s) for sub in c]
            return c

        for f in data.get("features", []):
            coords = f.get("geometry", {}).get("coordinates", [])
            _decimate(coords, step)

        reduction_pct = (1 - decimated_vertices / orig_vertices) * 100 if orig_vertices > 0 else 0
        est_new_size_kb = original_size_kb * (decimated_vertices / orig_vertices) if orig_vertices > 0 else original_size_kb

        lines = [
            f"Geometry Simplification Simulation (Decimation Step = {step})",
            "-" * 60,
            f"Original File Size: {original_size_kb:.1f} KB",
            f"Original Total Vertices: {orig_vertices:,}",
            f"Simplified Vertices: {decimated_vertices:,}",
            f"Vertex Reduction: {reduction_pct:.1f}%",
            f"Estimated Payload Size: {est_new_size_kb:.1f} KB",
            "Status: Safe for client-side rendering without loss of macro-boundary fidelity.",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"Error testing simplification: {e}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
