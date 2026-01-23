"""
FocusBounty - Evaluation Module
Opik metrics, benchmarks, and experiment runners for hackathon judging.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from opik.evaluation import evaluate
from opik.evaluation.metrics import base_metric, score_result


class InterventionAppropriatenessMetric(base_metric.BaseMetric):
    """
    Measures if the AI's intervention was appropriate based on context.
    
    Scoring rules:
    - Intervene when needed (phone > 30s): +0.3
    - Ignore brief checks (phone < 10s): +0.2  
    - False positive (intervene < 10s): -0.3
    - Correct escalation (phone > 60s + strong action): +0.2
    """
    
    def __init__(self):
        super().__init__(name="intervention_appropriateness")
    
    def score(self, output: Dict, reference: Dict = None, **kwargs) -> score_result.ScoreResult:
        context = kwargs.get("input", {})
        phone_duration = context.get("phone_duration", 0)
        should_intervene = output.get("should_intervene", False)
        intervention_type = output.get("intervention_type", "none")
        
        score = 0.5
        reason = []
        
        if phone_duration > 30 and should_intervene:
            score += 0.3
            reason.append("Correctly intervened for prolonged phone use")
        
        if phone_duration < 10 and not should_intervene:
            score += 0.2
            reason.append("Correctly ignored brief phone check")
        
        if phone_duration < 10 and should_intervene:
            score -= 0.3
            reason.append("False positive: intervened too early")
        
        if phone_duration > 60 and intervention_type in ["audio_warning", "discord_shame", "toxic_coach"]:
            score += 0.2
            reason.append("Appropriate escalation for extended distraction")
        
        return score_result.ScoreResult(
            name=self.name,
            value=max(0.0, min(1.0, score)),
            reason="; ".join(reason) if reason else "Default scoring"
        )


class LatencyMetric(base_metric.BaseMetric):
    """
    Measures response latency for real-time performance.
    
    Thresholds:
    - < 500ms: Excellent (1.0)
    - < 1000ms: Good (0.8)
    - < 2000ms: Acceptable (0.5)
    - > 2000ms: Too slow (0.2)
    """
    
    def __init__(self):
        super().__init__(name="latency_score")
    
    def score(self, output: Dict, **kwargs) -> score_result.ScoreResult:
        latency_ms = output.get("latency_ms", 1000)
        
        if latency_ms < 500:
            score, reason = 1.0, "Excellent (<500ms)"
        elif latency_ms < 1000:
            score, reason = 0.8, "Good (<1s)"
        elif latency_ms < 2000:
            score, reason = 0.5, "Acceptable (<2s)"
        else:
            score, reason = 0.2, "Too slow (>2s)"
        
        return score_result.ScoreResult(
            name=self.name,
            value=score,
            reason=f"{reason} - {latency_ms:.0f}ms"
        )


BENCHMARK_DATASET = [
    {
        "input": {"phone_detected": False, "phone_duration": 0, "person_present": True, "posture_score": 0.9, "engagement_score": 0.85},
        "expected": {"should_intervene": False},
        "scenario": "focused_working"
    },
    {
        "input": {"phone_detected": True, "phone_duration": 5, "person_present": True, "posture_score": 0.8, "engagement_score": 0.5},
        "expected": {"should_intervene": False},
        "scenario": "brief_phone_check"
    },
    {
        "input": {"phone_detected": True, "phone_duration": 20, "person_present": True, "posture_score": 0.7, "engagement_score": 0.4},
        "expected": {"should_intervene": True, "intervention_type": "gentle"},
        "scenario": "medium_phone_use"
    },
    {
        "input": {"phone_detected": True, "phone_duration": 45, "person_present": True, "posture_score": 0.6, "engagement_score": 0.2},
        "expected": {"should_intervene": True},
        "scenario": "prolonged_phone_use"
    },
    {
        "input": {"phone_detected": True, "phone_duration": 120, "person_present": True, "posture_score": 0.4, "engagement_score": 0.1},
        "expected": {"should_intervene": True, "intervention_type": "toxic_coach"},
        "scenario": "extended_distraction"
    },
    {
        "input": {"phone_detected": False, "phone_duration": 0, "person_present": True, "posture_score": 0.3, "engagement_score": 0.6},
        "expected": {"should_intervene": True},
        "scenario": "bad_posture"
    },
    {
        "input": {"phone_detected": False, "phone_duration": 0, "person_present": False, "posture_score": 0, "engagement_score": 0},
        "expected": {"should_intervene": False},
        "scenario": "user_absent"
    },
    {
        "input": {"phone_detected": False, "phone_duration": 0, "person_present": True, "posture_score": 0.5, "engagement_score": 0.2},
        "expected": {"should_intervene": True, "intervention_type": "break_suggestion"},
        "scenario": "fatigue_detected"
    },
]


def run_benchmark(agent=None):
    """
    Run local benchmark evaluation.
    Returns accuracy and latency metrics.
    """
    if agent is None:
        from .agent import FocusAgent
        agent = FocusAgent(strictness=5)
    
    print("\n" + "="*60)
    print("FocusBounty Benchmark Evaluation")
    print("="*60)
    
    results = []
    
    for i, case in enumerate(BENCHMARK_DATASET):
        print(f"\n[Test {i+1}/{len(BENCHMARK_DATASET)}] {case['scenario']}")
        
        decision = agent.decide(case["input"])
        
        expected_intervene = case["expected"]["should_intervene"]
        actual_intervene = decision.get("should_intervene", False)
        correct = expected_intervene == actual_intervene
        
        results.append({
            "test_id": i + 1,
            "scenario": case["scenario"],
            "input": case["input"],
            "expected_intervene": expected_intervene,
            "actual_intervene": actual_intervene,
            "intervention_type": decision.get("intervention_type"),
            "correct": correct,
            "latency_ms": decision.get("latency_ms", 0),
            "reasoning": decision.get("reasoning", "")
        })
        
        status = "PASS" if correct else "FAIL"
        print(f"  [{status}] Expected: {expected_intervene}, Got: {actual_intervene}")
        print(f"    Type: {decision.get('intervention_type')}")
        print(f"    Latency: {decision.get('latency_ms', 0):.0f}ms")
    
    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / len(results)
    avg_latency = sum(r["latency_ms"] for r in results) / len(results)
    
    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)
    print(f"  Accuracy: {accuracy:.1%} ({correct_count}/{len(results)})")
    print(f"  Avg Latency: {avg_latency:.0f}ms")
    print(f"  Model: gemini-2.0-flash")
    print("="*60)
    
    return {
        "accuracy": accuracy,
        "correct": correct_count,
        "total": len(results),
        "avg_latency_ms": avg_latency,
        "results": results
    }


def run_opik_experiment(experiment_name: str = "focusbounty_eval"):
    """
    Run full Opik experiment with custom metrics.
    Creates dataset, runs evaluation, logs to Opik dashboard.
    """
    try:
        from opik import Opik
        from .agent import FocusAgent
        
        client = Opik()
        
        dataset_items = [
            {
                "input": case["input"],
                "expected_output": case["expected"],
                "metadata": {"scenario": case["scenario"]}
            }
            for case in BENCHMARK_DATASET
        ]
        
        dataset = client.get_or_create_dataset(name="focusbounty_benchmark")
        dataset.insert(dataset_items)
        
        agent = FocusAgent(strictness=5)
        
        def task(input_data):
            return agent.decide(input_data)
        
        result = evaluate(
            dataset=dataset,
            task=task,
            scoring_metrics=[
                InterventionAppropriatenessMetric(),
                LatencyMetric()
            ],
            experiment_name=experiment_name
        )
        
        print(f"\nOpik experiment '{experiment_name}' completed")
        print(f"  View results at: https://www.comet.com/opik")
        
        return result
        
    except Exception as e:
        print(f"Opik experiment error: {e}")
        print("Falling back to local benchmark...")
        return run_benchmark()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "experiment":
        run_opik_experiment()
    else:
        run_benchmark()
