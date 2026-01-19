#!/usr/bin/env python3
"""
KSTAR Database - Long-term Memory for NEOLAF Agents

Provides CRUD operations for K* entries and knowledge management.

Storage:
- episodes/     - KSTAR episode entries (JSON files)
- knowledge/    - Semantic knowledge (indexed)
- skills/       - Generated skill templates

Usage:
    from kstar_db import KSTARDatabase

    db = KSTARDatabase("./db")

    # Create entry
    entry_id = db.create(kstar_entry)

    # Read entry
    entry = db.read(entry_id)

    # Query entries
    results = db.query(domain="programming", success=True)

    # Update entry
    db.update(entry_id, {"R.learning.lessons": ["new lesson"]})

    # Delete entry
    db.delete(entry_id)

    # Export to xAPI
    statements = db.export_xapi(entry_ids)
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
import hashlib


@dataclass
class QueryResult:
    """Result of a database query."""
    entries: List[Dict]
    total: int
    offset: int
    limit: int


@dataclass
class KSTAREntry:
    """KSTAR entry data structure."""
    K: Dict[str, Any]
    S: Dict[str, Any]
    T: Dict[str, Any]
    A: Dict[str, Any]
    R: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: f"kstar_{uuid.uuid4()}")

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "KSTAREntry":
        return cls(**data)


class KSTARDatabase:
    """
    File-based KSTAR entry database.

    Provides persistent storage and querying for K* entries.
    Uses JSON files for simplicity and portability.
    """

    SCHEMA_VERSION = "1.0.0"

    def __init__(self, db_path: str):
        """
        Initialize database.

        Args:
            db_path: Path to database directory
        """
        self.db_path = Path(db_path)
        self.episodes_path = self.db_path / "episodes"
        self.knowledge_path = self.db_path / "knowledge"
        self.index_path = self.db_path / "index"

        # Create directories
        self.episodes_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_path.mkdir(parents=True, exist_ok=True)
        self.index_path.mkdir(parents=True, exist_ok=True)

        # Load or create index
        self._index = self._load_index()

    # ==================== CRUD Operations ====================

    def create(self, entry: Dict | KSTAREntry) -> str:
        """
        Create a new KSTAR entry.

        Args:
            entry: Entry data (dict or KSTAREntry)

        Returns:
            Entry ID
        """
        if isinstance(entry, KSTAREntry):
            entry_dict = entry.to_dict()
        else:
            entry_dict = entry

        # Generate ID if not present
        if "id" not in entry_dict:
            entry_dict["id"] = f"kstar_{uuid.uuid4()}"

        # Add metadata
        now = datetime.now(timezone.utc).isoformat()
        if "metadata" not in entry_dict:
            entry_dict["metadata"] = {}

        entry_dict["metadata"]["created_at"] = now
        entry_dict["metadata"]["version"] = self.SCHEMA_VERSION

        # Save to file
        entry_id = entry_dict["id"]
        file_path = self.episodes_path / f"{entry_id}.json"

        with open(file_path, "w") as f:
            json.dump(entry_dict, f, indent=2, default=str)

        # Update index
        self._add_to_index(entry_dict)

        return entry_id

    def read(self, entry_id: str) -> Optional[Dict]:
        """
        Read a KSTAR entry by ID.

        Args:
            entry_id: Entry ID

        Returns:
            Entry dict or None if not found
        """
        file_path = self.episodes_path / f"{entry_id}.json"

        if not file_path.exists():
            return None

        with open(file_path) as f:
            return json.load(f)

    def update(self, entry_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a KSTAR entry.

        Args:
            entry_id: Entry ID
            updates: Dict of updates (supports dot notation paths)

        Returns:
            True if updated, False if not found
        """
        entry = self.read(entry_id)
        if not entry:
            return False

        # Apply updates (support dot notation)
        for path, value in updates.items():
            self._set_nested(entry, path, value)

        # Update timestamp
        entry["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Save
        file_path = self.episodes_path / f"{entry_id}.json"
        with open(file_path, "w") as f:
            json.dump(entry, f, indent=2, default=str)

        # Update index
        self._add_to_index(entry)

        return True

    def delete(self, entry_id: str) -> bool:
        """
        Delete a KSTAR entry.

        Args:
            entry_id: Entry ID

        Returns:
            True if deleted, False if not found
        """
        file_path = self.episodes_path / f"{entry_id}.json"

        if not file_path.exists():
            return False

        file_path.unlink()

        # Remove from index
        self._remove_from_index(entry_id)

        return True

    # ==================== Query Operations ====================

    def query(
        self,
        domain: Optional[str] = None,
        goal: Optional[str] = None,
        success: Optional[bool] = None,
        mode: Optional[str] = None,
        tags: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> QueryResult:
        """
        Query KSTAR entries with filters.

        Args:
            domain: Filter by domain type (S.S_D.domain_type)
            goal: Filter by goal (substring match)
            success: Filter by success status
            mode: Filter by mode (LEARNING/PERFORMANCE)
            tags: Filter by tags (metadata.tags)
            date_from: Filter by created_at >= date
            date_to: Filter by created_at <= date
            limit: Max results
            offset: Skip first N results

        Returns:
            QueryResult with matching entries
        """
        results = []

        for entry_file in self.episodes_path.glob("kstar_*.json"):
            with open(entry_file) as f:
                entry = json.load(f)

            # Apply filters
            if domain and self._get_nested(entry, "S.S_D.domain_type") != domain:
                continue

            if goal and goal.lower() not in self._get_nested(entry, "T.goal", "").lower():
                continue

            if success is not None:
                entry_success = self._get_nested(entry, "R.observation.success")
                if entry_success != success:
                    continue

            if mode and self._get_nested(entry, "S.S_P.mode") != mode:
                continue

            if tags:
                entry_tags = self._get_nested(entry, "metadata.tags", [])
                if not any(t in entry_tags for t in tags):
                    continue

            if date_from:
                created = self._get_nested(entry, "metadata.created_at", "")
                if created < date_from:
                    continue

            if date_to:
                created = self._get_nested(entry, "metadata.created_at", "")
                if created > date_to:
                    continue

            results.append(entry)

        # Sort by created_at descending
        results.sort(
            key=lambda e: e.get("metadata", {}).get("created_at", ""),
            reverse=True
        )

        total = len(results)

        # Apply pagination
        results = results[offset:offset + limit]

        return QueryResult(
            entries=results,
            total=total,
            offset=offset,
            limit=limit
        )

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Full-text search across entries.

        Args:
            query: Search query
            limit: Max results

        Returns:
            Matching entries
        """
        query_lower = query.lower()
        results = []
        scores = []

        for entry_file in self.episodes_path.glob("kstar_*.json"):
            with open(entry_file) as f:
                entry = json.load(f)

            # Simple scoring based on matches
            text = json.dumps(entry).lower()
            score = text.count(query_lower)

            if score > 0:
                results.append(entry)
                scores.append(score)

        # Sort by score
        sorted_results = [e for _, e in sorted(zip(scores, results), reverse=True)]

        return sorted_results[:limit]

    def get_by_tags(self, tags: List[str], match_all: bool = False) -> List[Dict]:
        """
        Get entries by tags.

        Args:
            tags: Tags to match
            match_all: If True, entry must have all tags

        Returns:
            Matching entries
        """
        results = []

        for entry_file in self.episodes_path.glob("kstar_*.json"):
            with open(entry_file) as f:
                entry = json.load(f)

            entry_tags = set(entry.get("metadata", {}).get("tags", []))

            if match_all:
                if set(tags).issubset(entry_tags):
                    results.append(entry)
            else:
                if entry_tags.intersection(tags):
                    results.append(entry)

        return results

    # ==================== Knowledge Operations ====================

    def get_knowledge(self, domain: Optional[str] = None) -> Dict:
        """
        Get aggregated knowledge from episodes.

        Args:
            domain: Optional domain filter

        Returns:
            Aggregated knowledge dict
        """
        knowledge = {
            "episodes_count": 0,
            "success_rate": 0.0,
            "domains": {},
            "lessons": [],
            "skills_used": {},
            "confidence": {}
        }

        query_result = self.query(domain=domain, limit=10000)
        entries = query_result.entries

        if not entries:
            return knowledge

        knowledge["episodes_count"] = len(entries)

        # Aggregate
        successes = 0
        for entry in entries:
            # Success rate
            if self._get_nested(entry, "R.observation.success"):
                successes += 1

            # Domain stats
            domain_type = self._get_nested(entry, "S.S_D.domain_type", "unknown")
            if domain_type not in knowledge["domains"]:
                knowledge["domains"][domain_type] = {"count": 0, "successes": 0}
            knowledge["domains"][domain_type]["count"] += 1
            if self._get_nested(entry, "R.observation.success"):
                knowledge["domains"][domain_type]["successes"] += 1

            # Lessons
            lessons = self._get_nested(entry, "R.learning.lessons", [])
            knowledge["lessons"].extend(lessons)

            # Skills used
            skills = self._get_nested(entry, "K.skills_available", [])
            for skill in skills:
                knowledge["skills_used"][skill] = knowledge["skills_used"].get(skill, 0) + 1

        knowledge["success_rate"] = successes / len(entries) if entries else 0

        # Compute confidence per domain
        for domain_type, stats in knowledge["domains"].items():
            if stats["count"] > 0:
                knowledge["confidence"][domain_type] = stats["successes"] / stats["count"]

        return knowledge

    def extract_lessons(
        self,
        domain: Optional[str] = None,
        min_prediction_error: float = 0.3
    ) -> List[Dict]:
        """
        Extract lessons from episodes with high prediction error.

        Args:
            domain: Optional domain filter
            min_prediction_error: Minimum error to include

        Returns:
            List of lesson dicts
        """
        lessons = []

        query_result = self.query(domain=domain, limit=10000)

        for entry in query_result.entries:
            pred_error = self._get_nested(entry, "R.prediction_error", 0)
            if pred_error >= min_prediction_error:
                entry_lessons = self._get_nested(entry, "R.learning.lessons", [])
                aar_lessons = self._get_nested(entry, "R.aar.lessons_learned", [])

                for lesson in entry_lessons + aar_lessons:
                    lessons.append({
                        "lesson": lesson,
                        "entry_id": entry["id"],
                        "domain": self._get_nested(entry, "S.S_D.domain_type"),
                        "prediction_error": pred_error,
                        "goal": self._get_nested(entry, "T.goal")
                    })

        return lessons

    # ==================== xAPI Export ====================

    def export_xapi(
        self,
        entry_ids: Optional[List[str]] = None,
        query_params: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Export entries as xAPI statements.

        Args:
            entry_ids: Specific entries to export
            query_params: Or query parameters to select entries

        Returns:
            List of xAPI statements
        """
        statements = []

        # Get entries
        if entry_ids:
            entries = [self.read(eid) for eid in entry_ids if self.read(eid)]
        elif query_params:
            result = self.query(**query_params)
            entries = result.entries
        else:
            result = self.query(limit=10000)
            entries = result.entries

        # Convert each entry to xAPI
        for entry in entries:
            statement = self._to_xapi_statement(entry)
            statements.append(statement)

        return statements

    def _to_xapi_statement(self, entry: Dict) -> Dict:
        """Convert KSTAR entry to xAPI statement."""
        # Map KSTAR stage to xAPI verb
        stage = self._get_nested(entry, "T.stage", "completed")
        verb_map = {
            "understand": ("https://neolaf.org/xapi/verbs/understood", "understood"),
            "plan": ("https://neolaf.org/xapi/verbs/planned", "planned"),
            "execute": ("https://neolaf.org/xapi/verbs/executed", "executed"),
            "validate": ("https://neolaf.org/xapi/verbs/validated", "validated"),
            "reflect": ("https://neolaf.org/xapi/verbs/reflected", "reflected"),
            "complete": ("http://adlnet.gov/expapi/verbs/completed", "completed")
        }
        verb_id, verb_display = verb_map.get(stage, verb_map["complete"])

        # Build statement
        statement = {
            "id": str(uuid.uuid4()),
            "actor": {
                "objectType": "Agent",
                "name": self._get_nested(entry, "S.S_A.id", "agent"),
                "account": {
                    "homePage": "https://neolaf.org/agents",
                    "name": self._get_nested(entry, "S.S_A.id", "agent")
                }
            },
            "verb": {
                "id": verb_id,
                "display": {"en-US": verb_display}
            },
            "object": {
                "objectType": "Activity",
                "id": f"https://neolaf.org/activities/{entry['id']}",
                "definition": {
                    "type": "https://neolaf.org/xapi/activity-types/kstar-episode",
                    "name": {"en-US": self._get_nested(entry, "T.goal", "task")},
                    "description": {"en-US": self._get_nested(entry, "T.goal", "")},
                    "extensions": {
                        "https://neolaf.org/xapi/extensions/kstar-entry-id": entry["id"],
                        "https://neolaf.org/xapi/extensions/task-goal": self._get_nested(entry, "T.goal"),
                        "https://neolaf.org/xapi/extensions/domain-type": self._get_nested(entry, "S.S_D.domain_type")
                    }
                }
            },
            "result": {
                "success": self._get_nested(entry, "R.observation.success", False),
                "completion": stage == "complete",
                "extensions": {
                    "https://neolaf.org/xapi/extensions/prediction-error": self._get_nested(entry, "R.prediction_error", 0),
                    "https://neolaf.org/xapi/extensions/lessons-learned": self._get_nested(entry, "R.learning.lessons", [])
                }
            },
            "context": {
                "extensions": {
                    "https://neolaf.org/xapi/extensions/mode": self._get_nested(entry, "S.S_P.mode"),
                    "https://neolaf.org/xapi/extensions/workflow-type": self._get_nested(entry, "S.S_P.workflow_type")
                }
            },
            "timestamp": self._get_nested(entry, "metadata.created_at", datetime.now(timezone.utc).isoformat())
        }

        return statement

    # ==================== Utility Methods ====================

    def list_all(self, limit: int = 100) -> List[str]:
        """List all entry IDs."""
        ids = []
        for entry_file in self.episodes_path.glob("kstar_*.json"):
            ids.append(entry_file.stem)
        return ids[:limit]

    def count(self) -> int:
        """Count total entries."""
        return len(list(self.episodes_path.glob("kstar_*.json")))

    def stats(self) -> Dict:
        """Get database statistics."""
        entries = self.query(limit=10000).entries

        return {
            "total_entries": len(entries),
            "domains": list(set(
                self._get_nested(e, "S.S_D.domain_type", "unknown")
                for e in entries
            )),
            "success_count": sum(
                1 for e in entries
                if self._get_nested(e, "R.observation.success")
            ),
            "modes": {
                "LEARNING": sum(1 for e in entries if self._get_nested(e, "S.S_P.mode") == "LEARNING"),
                "PERFORMANCE": sum(1 for e in entries if self._get_nested(e, "S.S_P.mode") == "PERFORMANCE")
            },
            "db_path": str(self.db_path)
        }

    # ==================== Internal Methods ====================

    def _load_index(self) -> Dict:
        """Load or create index."""
        index_file = self.index_path / "main.json"
        if index_file.exists():
            with open(index_file) as f:
                return json.load(f)
        return {"entries": {}, "domains": {}, "tags": {}}

    def _save_index(self):
        """Save index to disk."""
        index_file = self.index_path / "main.json"
        with open(index_file, "w") as f:
            json.dump(self._index, f, indent=2)

    def _add_to_index(self, entry: Dict):
        """Add entry to index."""
        entry_id = entry["id"]
        domain = self._get_nested(entry, "S.S_D.domain_type", "unknown")
        tags = self._get_nested(entry, "metadata.tags", [])

        self._index["entries"][entry_id] = {
            "domain": domain,
            "tags": tags,
            "created_at": self._get_nested(entry, "metadata.created_at")
        }

        # Domain index
        if domain not in self._index["domains"]:
            self._index["domains"][domain] = []
        if entry_id not in self._index["domains"][domain]:
            self._index["domains"][domain].append(entry_id)

        # Tag index
        for tag in tags:
            if tag not in self._index["tags"]:
                self._index["tags"][tag] = []
            if entry_id not in self._index["tags"][tag]:
                self._index["tags"][tag].append(entry_id)

        self._save_index()

    def _remove_from_index(self, entry_id: str):
        """Remove entry from index."""
        if entry_id in self._index["entries"]:
            info = self._index["entries"].pop(entry_id)

            # Remove from domain index
            domain = info.get("domain")
            if domain in self._index["domains"]:
                self._index["domains"][domain] = [
                    eid for eid in self._index["domains"][domain]
                    if eid != entry_id
                ]

            # Remove from tag index
            for tag in info.get("tags", []):
                if tag in self._index["tags"]:
                    self._index["tags"][tag] = [
                        eid for eid in self._index["tags"][tag]
                        if eid != entry_id
                    ]

            self._save_index()

    def _get_nested(self, obj: Dict, path: str, default: Any = None) -> Any:
        """Get value at nested path."""
        parts = path.split(".")
        current = obj
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def _set_nested(self, obj: Dict, path: str, value: Any):
        """Set value at nested path."""
        parts = path.split(".")
        current = obj
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value


# ==================== CLI Interface ====================

def main():
    """Command-line interface for KSTAR database."""
    import argparse

    parser = argparse.ArgumentParser(description="KSTAR Database CLI")
    parser.add_argument("--db", default="./db", help="Database path")

    subparsers = parser.add_subparsers(dest="command")

    # Stats command
    subparsers.add_parser("stats", help="Show database statistics")

    # List command
    list_parser = subparsers.add_parser("list", help="List entries")
    list_parser.add_argument("--limit", type=int, default=20)

    # Read command
    read_parser = subparsers.add_parser("read", help="Read entry")
    read_parser.add_argument("entry_id", help="Entry ID")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query entries")
    query_parser.add_argument("--domain", help="Filter by domain")
    query_parser.add_argument("--success", type=bool, help="Filter by success")
    query_parser.add_argument("--mode", help="Filter by mode")
    query_parser.add_argument("--limit", type=int, default=20)

    # Export command
    export_parser = subparsers.add_parser("export-xapi", help="Export to xAPI")
    export_parser.add_argument("--output", default="xapi-statements.json")
    export_parser.add_argument("--domain", help="Filter by domain")

    # Knowledge command
    knowledge_parser = subparsers.add_parser("knowledge", help="Get aggregated knowledge")
    knowledge_parser.add_argument("--domain", help="Filter by domain")

    args = parser.parse_args()

    db = KSTARDatabase(args.db)

    if args.command == "stats":
        stats = db.stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "list":
        ids = db.list_all(limit=args.limit)
        for eid in ids:
            print(eid)

    elif args.command == "read":
        entry = db.read(args.entry_id)
        if entry:
            print(json.dumps(entry, indent=2))
        else:
            print(f"Entry not found: {args.entry_id}")

    elif args.command == "query":
        result = db.query(
            domain=args.domain,
            success=args.success,
            mode=args.mode,
            limit=args.limit
        )
        print(f"Found {result.total} entries (showing {len(result.entries)}):")
        for entry in result.entries:
            print(f"  {entry['id']}: {entry.get('T', {}).get('goal', 'N/A')[:50]}")

    elif args.command == "export-xapi":
        statements = db.export_xapi(
            query_params={"domain": args.domain} if args.domain else None
        )
        with open(args.output, "w") as f:
            json.dump(statements, f, indent=2)
        print(f"Exported {len(statements)} statements to {args.output}")

    elif args.command == "knowledge":
        knowledge = db.get_knowledge(domain=args.domain)
        print(json.dumps(knowledge, indent=2))

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
