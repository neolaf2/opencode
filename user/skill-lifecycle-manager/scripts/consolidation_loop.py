#!/usr/bin/env python3
"""
Consolidation Loop

Implements the overnight (or periodic) consolidation process that transforms
raw K-STAR episodes into executable, generalizable skill objects.

The consolidation loop:
1. Scans for promotion candidates
2. Scans for generalization opportunities
3. Scans for split candidates (bimodal failures)
4. Scans for merge candidates (duplicates)
5. Scans for composition opportunities
6. Scans for quarantine needs
7. Updates retrieval indices
8. (Optional) Updates neural embeddings

This solves the "flat DB" problem by continuously restructuring the skill graph.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import logging

from lifecycle_manager import (
    SkillLifecycleManager, Skill, Episode, LifecycleState, STATE_NAMES
)
from rewrite_rules import (
    RewriteEngine, rule_promote, rule_generalize, rule_learn_boundaries,
    rule_split, rule_merge, rule_compose, rule_quarantine, rule_deprecate,
    find_frequent_sequences, compute_skill_overlap
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class ConsolidationConfig:
    """Configuration for the consolidation loop."""
    # Promotion thresholds
    min_executions_for_operational: int = 5
    success_rate_for_operational: float = 0.8
    
    # Generalization thresholds
    min_episodes_for_generalization: int = 2
    
    # Split thresholds
    bimodal_difference_threshold: float = 0.3
    min_episodes_per_cluster: int = 2
    
    # Merge thresholds
    merge_overlap_threshold: float = 0.7
    
    # Composition thresholds
    min_sequence_frequency: int = 3
    
    # Quarantine thresholds
    failure_rate_for_quarantine: float = 0.7
    min_failures_for_quarantine: int = 3
    days_since_success_for_quarantine: int = 30
    
    # Deprecation thresholds
    days_inactive_for_deprecation: int = 90


@dataclass
class ConsolidationReport:
    """Report from a consolidation run."""
    run_id: str
    started_at: datetime
    completed_at: datetime
    
    # Counts
    skills_scanned: int = 0
    episodes_processed: int = 0
    
    # Actions taken
    promotions: List[Dict] = field(default_factory=list)
    generalizations: List[Dict] = field(default_factory=list)
    boundaries_learned: List[Dict] = field(default_factory=list)
    splits: List[Dict] = field(default_factory=list)
    merges: List[Dict] = field(default_factory=list)
    compositions: List[Dict] = field(default_factory=list)
    quarantines: List[Dict] = field(default_factory=list)
    deprecations: List[Dict] = field(default_factory=list)
    
    # Summary
    total_actions: int = 0
    errors: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSOLIDATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

class ConsolidationLoop:
    """
    The overnight consolidation process.
    
    Transforms raw episodes into structured, generalizable skills
    through systematic application of rewrite rules.
    """
    
    def __init__(
        self,
        manager: SkillLifecycleManager,
        config: ConsolidationConfig = None
    ):
        self.manager = manager
        self.config = config or ConsolidationConfig()
        self.rewrite_engine = RewriteEngine(manager)
    
    def run(self) -> ConsolidationReport:
        """
        Execute a full consolidation cycle.
        """
        from uuid import uuid4
        
        report = ConsolidationReport(
            run_id=str(uuid4()),
            started_at=datetime.now(),
            completed_at=datetime.now()  # Will be updated
        )
        
        logger.info(f"Starting consolidation run {report.run_id}")
        
        try:
            # Phase 1: Scan for promotions
            self._phase_promotions(report)
            
            # Phase 2: Scan for generalizations
            self._phase_generalizations(report)
            
            # Phase 3: Learn boundaries
            self._phase_boundary_learning(report)
            
            # Phase 4: Scan for splits
            self._phase_splits(report)
            
            # Phase 5: Scan for merges
            self._phase_merges(report)
            
            # Phase 6: Scan for compositions
            self._phase_compositions(report)
            
            # Phase 7: Scan for quarantine needs
            self._phase_quarantine_check(report)
            
            # Phase 8: Scan for deprecation needs
            self._phase_deprecation_check(report)
            
            # Phase 9: Update indices
            self._phase_update_indices(report)
            
        except Exception as e:
            report.errors.append(str(e))
            logger.error(f"Consolidation error: {e}")
        
        report.completed_at = datetime.now()
        report.total_actions = (
            len(report.promotions) +
            len(report.generalizations) +
            len(report.boundaries_learned) +
            len(report.splits) +
            len(report.merges) +
            len(report.compositions) +
            len(report.quarantines) +
            len(report.deprecations)
        )
        
        logger.info(f"Consolidation complete: {report.total_actions} actions taken")
        return report
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Promotions
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_promotions(self, report: ConsolidationReport):
        """Scan for skills ready to be promoted."""
        logger.info("Phase 1: Scanning for promotions")
        
        # Candidate → Validated
        for skill in self.manager.get_skills_by_state(LifecycleState.CANDIDATE):
            episodes = self._get_skill_episodes(skill)
            successful = [e for e in episodes if e.success]
            
            if successful:
                # Promote on first success
                if self.manager.promote_to_validated(skill, successful[0]):
                    report.promotions.append({
                        "skill_id": skill.skill_id,
                        "from": "Candidate",
                        "to": "Validated",
                        "evidence": successful[0].episode_id
                    })
        
        # Validated → Generalizing
        for skill in self.manager.get_skills_by_state(LifecycleState.VALIDATED):
            if skill.total_executions >= 2:
                if self.manager.promote_to_generalizing(skill):
                    report.promotions.append({
                        "skill_id": skill.skill_id,
                        "from": "Validated",
                        "to": "Generalizing"
                    })
        
        # Generalizing → Operational
        for skill in self.manager.get_skills_by_state(LifecycleState.GENERALIZING):
            if self.manager.promote_to_operational(
                skill,
                success_rate_threshold=self.config.success_rate_for_operational,
                min_executions=self.config.min_executions_for_operational
            ):
                report.promotions.append({
                    "skill_id": skill.skill_id,
                    "from": "Generalizing",
                    "to": "Operational",
                    "success_rate": skill.success_rate
                })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Generalizations
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_generalizations(self, report: ConsolidationReport):
        """Scan for generalization opportunities."""
        logger.info("Phase 2: Scanning for generalizations")
        
        for skill in self.manager.get_skills_by_state(LifecycleState.VALIDATED):
            episodes = self._get_skill_episodes(skill)
            
            if len(episodes) >= self.config.min_episodes_for_generalization:
                if rule_generalize(self.manager, skill, episodes):
                    report.generalizations.append({
                        "skill_id": skill.skill_id,
                        "parameters_added": [p.name for p in skill.parameter_schema]
                    })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Boundary Learning
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_boundary_learning(self, report: ConsolidationReport):
        """Learn applicability boundaries from success/failure patterns."""
        logger.info("Phase 3: Learning boundaries")
        
        for skill in self.manager.get_skills_by_state(LifecycleState.GENERALIZING):
            episodes = self._get_skill_episodes(skill)
            
            if rule_learn_boundaries(self.manager, skill, episodes):
                report.boundaries_learned.append({
                    "skill_id": skill.skill_id,
                    "conditions_added": len(skill.applicability_conditions),
                    "forbidden_added": len(skill.do_not_apply_when)
                })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4: Splits
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_splits(self, report: ConsolidationReport):
        """Scan for skills that should be split."""
        logger.info("Phase 4: Scanning for splits")
        
        for skill in list(self.manager.skills.values()):
            if skill.lifecycle_state not in [LifecycleState.GENERALIZING, LifecycleState.OPERATIONAL]:
                continue
            
            episodes = self._get_skill_episodes(skill)
            
            if len(episodes) < 4:
                continue
            
            new_skills = rule_split(self.manager, skill, episodes)
            if new_skills:
                report.splits.append({
                    "original_skill_id": skill.skill_id,
                    "new_skill_ids": [s.skill_id for s in new_skills]
                })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 5: Merges
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_merges(self, report: ConsolidationReport):
        """Scan for duplicate skills to merge."""
        logger.info("Phase 5: Scanning for merges")
        
        operational = self.manager.get_operational_skills()
        merged_ids = set()
        
        for i, skill_a in enumerate(operational):
            if skill_a.skill_id in merged_ids:
                continue
            
            for skill_b in operational[i+1:]:
                if skill_b.skill_id in merged_ids:
                    continue
                
                overlap = compute_skill_overlap(skill_a, skill_b)
                
                if overlap >= self.config.merge_overlap_threshold:
                    canonical = rule_merge(
                        self.manager, skill_a, skill_b,
                        merge_threshold=self.config.merge_overlap_threshold
                    )
                    if canonical:
                        deprecated_id = skill_b.skill_id if canonical == skill_a else skill_a.skill_id
                        merged_ids.add(deprecated_id)
                        report.merges.append({
                            "merged_skill_id": deprecated_id,
                            "canonical_skill_id": canonical.skill_id,
                            "overlap": overlap
                        })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 6: Compositions
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_compositions(self, report: ConsolidationReport):
        """Scan for frequent skill sequences to compose."""
        logger.info("Phase 6: Scanning for compositions")
        
        all_episodes = list(self.manager.episodes.values())
        frequent = find_frequent_sequences(
            all_episodes,
            min_frequency=self.config.min_sequence_frequency
        )
        
        for sequence, frequency in frequent[:5]:  # Top 5 sequences
            # Check if macro already exists
            sequence_key = "_".join(sequence)
            existing_macro = any(
                s.component_skills == sequence
                for s in self.manager.skills.values()
            )
            
            if not existing_macro:
                macro = rule_compose(
                    self.manager,
                    skill_ids=sequence,
                    macro_name=f"Composed: {sequence_key}",
                    macro_task={"type": "composed", "components": sequence}
                )
                if macro:
                    report.compositions.append({
                        "macro_skill_id": macro.skill_id,
                        "component_skills": sequence,
                        "frequency": frequency
                    })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 7: Quarantine Check
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_quarantine_check(self, report: ConsolidationReport):
        """Check for skills that should be quarantined."""
        logger.info("Phase 7: Checking for quarantine needs")
        
        now = datetime.now()
        
        for skill in list(self.manager.skills.values()):
            if skill.lifecycle_state in [LifecycleState.QUARANTINED, LifecycleState.DEPRECATED]:
                continue
            
            reasons = []
            
            # Check failure rate
            if skill.total_executions >= self.config.min_failures_for_quarantine:
                failure_rate = 1.0 - skill.success_rate
                if failure_rate >= self.config.failure_rate_for_quarantine:
                    reasons.append(f"High failure rate: {failure_rate:.1%}")
            
            # Check time since last success
            if skill.last_success:
                days_since = (now - skill.last_success).days
                if days_since >= self.config.days_since_success_for_quarantine:
                    if skill.last_failure and skill.last_failure > skill.last_success:
                        reasons.append(f"No success in {days_since} days")
            
            if reasons:
                episodes = self._get_skill_episodes(skill)
                failures = [e for e in episodes if not e.success]
                
                rule_quarantine(
                    self.manager, skill,
                    reason="; ".join(reasons),
                    evidence=failures[-3:]  # Last 3 failures
                )
                report.quarantines.append({
                    "skill_id": skill.skill_id,
                    "reason": reasons
                })
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 8: Deprecation Check
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_deprecation_check(self, report: ConsolidationReport):
        """Check for skills that should be deprecated."""
        logger.info("Phase 8: Checking for deprecation needs")
        
        now = datetime.now()
        inactive_threshold = timedelta(days=self.config.days_inactive_for_deprecation)
        
        for skill in list(self.manager.skills.values()):
            if skill.lifecycle_state in [LifecycleState.QUARANTINED, LifecycleState.DEPRECATED]:
                continue
            
            # Check if inactive
            last_activity = skill.last_modified
            if (now - last_activity) > inactive_threshold:
                # Check if superseded
                superseded_by = self._find_superseding_skill(skill)
                
                reason = f"Inactive for {self.config.days_inactive_for_deprecation}+ days"
                if superseded_by:
                    reason += f", superseded by {superseded_by}"
                
                rule_deprecate(self.manager, skill, reason, superseded_by)
                report.deprecations.append({
                    "skill_id": skill.skill_id,
                    "reason": reason,
                    "superseded_by": superseded_by
                })
    
    def _find_superseding_skill(self, skill: Skill) -> Optional[str]:
        """Find a skill that might supersede this one."""
        for other in self.manager.skills.values():
            if other.skill_id == skill.skill_id:
                continue
            if other.lifecycle_state == LifecycleState.DEPRECATED:
                continue
            
            # Check if other skill covers same capabilities better
            overlap = compute_skill_overlap(skill, other)
            if overlap > 0.8 and other.success_rate > skill.success_rate:
                return other.skill_id
        
        return None
    
    # ─────────────────────────────────────────────────────────────────────────
    # Phase 9: Update Indices
    # ─────────────────────────────────────────────────────────────────────────
    
    def _phase_update_indices(self, report: ConsolidationReport):
        """Update retrieval indices."""
        logger.info("Phase 9: Updating indices")
        
        # In a full implementation, this would:
        # 1. Rebuild situation→skill index
        # 2. Rebuild task→skill index
        # 3. Rebuild tool→skill index
        # 4. Update neural embeddings
        
        # For now, just count
        report.skills_scanned = len(self.manager.skills)
        report.episodes_processed = len(self.manager.episodes)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_skill_episodes(self, skill: Skill) -> List[Episode]:
        """Get all episodes for a skill."""
        return [
            self.manager.episodes[eid]
            for eid in skill.episode_ids
            if eid in self.manager.episodes
        ]


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT FORMATTING
# ═══════════════════════════════════════════════════════════════════════════════

def format_report(report: ConsolidationReport) -> str:
    """Format a consolidation report for display."""
    lines = [
        "═" * 70,
        "CONSOLIDATION REPORT",
        "═" * 70,
        f"Run ID: {report.run_id}",
        f"Started: {report.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Completed: {report.completed_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Duration: {(report.completed_at - report.started_at).total_seconds():.1f}s",
        "",
        f"Skills scanned: {report.skills_scanned}",
        f"Episodes processed: {report.episodes_processed}",
        f"Total actions: {report.total_actions}",
        "",
        "─" * 70,
        "ACTIONS TAKEN",
        "─" * 70,
    ]
    
    if report.promotions:
        lines.append(f"\n📈 Promotions ({len(report.promotions)}):")
        for p in report.promotions:
            lines.append(f"  • {p['skill_id']}: {p.get('from', '?')} → {p.get('to', '?')}")
    
    if report.generalizations:
        lines.append(f"\n🔄 Generalizations ({len(report.generalizations)}):")
        for g in report.generalizations:
            params = g.get('parameters_added', [])
            lines.append(f"  • {g['skill_id']}: +{len(params)} parameters")
    
    if report.boundaries_learned:
        lines.append(f"\n🎯 Boundaries Learned ({len(report.boundaries_learned)}):")
        for b in report.boundaries_learned:
            lines.append(f"  • {b['skill_id']}: +{b.get('conditions_added', 0)} conditions")
    
    if report.splits:
        lines.append(f"\n✂️ Splits ({len(report.splits)}):")
        for s in report.splits:
            lines.append(f"  • {s['original_skill_id']} → {len(s.get('new_skill_ids', []))} variants")
    
    if report.merges:
        lines.append(f"\n🔗 Merges ({len(report.merges)}):")
        for m in report.merges:
            lines.append(f"  • {m['merged_skill_id']} → {m['canonical_skill_id']}")
    
    if report.compositions:
        lines.append(f"\n🧩 Compositions ({len(report.compositions)}):")
        for c in report.compositions:
            lines.append(f"  • {c['macro_skill_id']}: {len(c.get('component_skills', []))} skills")
    
    if report.quarantines:
        lines.append(f"\n⚠️ Quarantines ({len(report.quarantines)}):")
        for q in report.quarantines:
            lines.append(f"  • {q['skill_id']}: {q.get('reason', ['?'])}")
    
    if report.deprecations:
        lines.append(f"\n🗃️ Deprecations ({len(report.deprecations)}):")
        for d in report.deprecations:
            lines.append(f"  • {d['skill_id']}: {d.get('reason', '?')}")
    
    if report.errors:
        lines.append(f"\n❌ Errors ({len(report.errors)}):")
        for e in report.errors:
            lines.append(f"  • {e}")
    
    lines.append("")
    lines.append("═" * 70)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Example usage
    print("Consolidation Loop Module")
    print("=" * 40)
    print()
    print("Usage:")
    print("  from consolidation_loop import ConsolidationLoop, ConsolidationConfig")
    print("  from lifecycle_manager import SkillLifecycleManager")
    print()
    print("  manager = SkillLifecycleManager()")
    print("  loop = ConsolidationLoop(manager)")
    print("  report = loop.run()")
    print("  print(format_report(report))")
