import os
import json
import re

report_path = r"d:\myproject\vesviet\content-audit-report.json"
base_dir = r"d:\myproject\vesviet\content"

def clean_spam():
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    spam_patterns = [
        re.compile(r"Database migration strategies for .*? follow the Strangler Fig pattern, gradually shifting traffic from legacy monolith tables to isolated microservice schemas without downtime\.(Database migration strategies for .*? follow the Strangler Fig pattern, gradually shifting traffic from legacy monolith tables to isolated microservice schemas without downtime\.)?", re.IGNORECASE),
        re.compile(r"When deploying .*? to production Kubernetes clusters, Horizontal Pod Autoscalers \(HPA\) scale replicas based on custom Prometheus queue depth metrics rather than raw CPU utilization\.", re.IGNORECASE),
        re.compile(r"E-commerce checkout flows in .*? use atomic inventory reservation locks with automatic expiration timers\. Unclaimed order locks release back into available stock after 15 minutes\.(E-commerce checkout flows in .*? use atomic inventory reservation locks with automatic expiration timers\. Unclaimed order locks release back into available stock after 15 minutes\.)?", re.IGNORECASE),
        re.compile(r"Observability in .*? combines structured JSON logging, trace span context propagation, and custom metric counters\. Alerting thresholds flag elevated error rates before customer impact occurs\.", re.IGNORECASE),
        re.compile(r"Load balancing in .*? employs least-connections algorithm routing with HTTP/2 multiplexed streams\. Connection keep-alive timeouts maintain efficient socket utilization\.", re.IGNORECASE),
        re.compile(r"Here are actionable answers on tuning Goroutine worker pools, channel backpressure, and multi-tier Redis caching topologies: regarding concurrency management, database locking, rate limiting algorithms, and microservices architecture trade-offs\.", re.IGNORECASE)
    ]

    cleaned_count = 0
    for file_info in report.get('affectedFiles', []):
        rel_path = file_info['file'].lstrip("\\/")
        full_path = os.path.join(base_dir, rel_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            orig_content = content
            for pattern in spam_patterns:
                content = pattern.sub("", content)
            
            # Clean up empty lines that might have been left behind
            content = re.sub(r'\n[ \t]*\n[ \t]*\n', '\n\n', content)
            
            if orig_content != content:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Cleaned {rel_path}")
                cleaned_count += 1
        else:
            print(f"File not found: {full_path}")
            
    print(f"\nTotal files cleaned: {cleaned_count}")

if __name__ == "__main__":
    clean_spam()
