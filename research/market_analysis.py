"""
CareCompass Market Research Analysis
Using Similarweb API to analyze the healthcare communication coaching market

This script analyzes:
1. Competitor landscape in healthcare communication training
2. AI traffic trends to healthcare/medical sites
3. Audience overlap between healthcare training platforms
"""

import json
import subprocess
from datetime import datetime

URL = "https://mcp.similarweb.com/"
API_KEY = "6b1f5842c65a4146a035b77689fa65b2"

def call_similarweb(tool: str, args: dict) -> dict:
    """Call Similarweb MCP endpoint."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    }
    
    raw = subprocess.run(
        ["curl", "-s", "-X", "POST", URL,
         "-H", f"api-key: {API_KEY}",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(body)],
        capture_output=True, text=True).stdout
    
    try:
        result = json.loads(raw)
        text = result["result"]["content"][0]["text"]
        # Strip banner prefix before JSON
        payload = json.loads(text[text.find("{"):])
        
        if "error" in payload:
            return {"error": payload["error"].get("error_message", "Unknown error")}
        
        return payload.get("data", payload)
    except Exception as e:
        return {"error": str(e)}


def analyze_domain(domain: str, label: str) -> dict:
    """Get traffic and engagement data for a domain."""
    print(f"\n📊 Analyzing {label}: {domain}")
    
    # Traffic and engagement
    traffic = call_similarweb("get-websites-traffic-and-engagement", {
        "domain": domain,
        "country": "us"
    })
    
    # AI traffic (how much traffic comes from AI assistants)
    ai_traffic = call_similarweb("get-ai-traffic-overview", {
        "domain": domain,
        "country": "us"
    })
    
    return {
        "domain": domain,
        "label": label,
        "traffic": traffic,
        "ai_traffic": ai_traffic
    }


def find_competitors(domain: str) -> dict:
    """Find similar sites and competitors."""
    print(f"\n🔍 Finding competitors for: {domain}")
    
    similar = call_similarweb("get-websites-similar-sites-agg", {
        "domain": domain,
        "country": "us"
    })
    
    return similar


def get_audience_overlap(domains: list) -> dict:
    """Get audience overlap between domains."""
    print(f"\n👥 Analyzing audience overlap...")
    
    # Use first domain as base
    overlap = call_similarweb("get-websites-audience-overlap-agg", {
        "domain": domains[0],
        "country": "us"
    })
    
    return overlap


def main():
    print("=" * 60)
    print("CareCompass Market Research Analysis")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # Key domains in healthcare communication/training space
    domains_to_analyze = [
        ("healthcaretrainingresource.com", "Healthcare Training Resource"),
        ("ahrq.gov", "AHRQ (Agency for Healthcare Research)"),
        ("ihi.org", "Institute for Healthcare Improvement"),
        ("jointcommission.org", "Joint Commission"),
        ("ama-assn.org", "American Medical Association"),
        ("healthstream.com", "HealthStream (Healthcare Learning)"),
        ("relias.com", "Relias (Healthcare Training)"),
    ]
    
    results = {
        "analysis_date": datetime.now().isoformat(),
        "domains": [],
        "competitors": {},
        "market_insights": []
    }
    
    # Analyze each domain
    for domain, label in domains_to_analyze:
        data = analyze_domain(domain, label)
        results["domains"].append(data)
        
        # Print summary
        traffic = data.get("traffic", {})
        if isinstance(traffic, dict) and "error" not in traffic:
            visits = traffic.get("visits", "N/A")
            print(f"  Monthly visits: {visits}")
        elif isinstance(traffic, list) and len(traffic) > 0:
            latest = traffic[0] if isinstance(traffic[0], dict) else {}
            visits = latest.get("visits", "N/A")
            print(f"  Monthly visits: {visits}")
        
        ai = data.get("ai_traffic", {})
        if isinstance(ai, dict) and "error" not in ai:
            print(f"  AI traffic data available: True")
        elif isinstance(ai, list) and len(ai) > 0:
            print(f"  AI traffic data available: True")
    
    # Find competitors for healthcare training
    print("\n" + "=" * 60)
    print("COMPETITOR ANALYSIS")
    print("=" * 60)
    
    competitors = find_competitors("healthstream.com")
    results["competitors"]["healthstream"] = competitors
    
    if "error" not in competitors:
        print("\nTop competitors to HealthStream:")
        similar_sites = competitors.get("similar_sites", [])[:10]
        for site in similar_sites:
            if isinstance(site, dict):
                print(f"  - {site.get('domain', site)}")
            else:
                print(f"  - {site}")
    
    # Market insights
    print("\n" + "=" * 60)
    print("MARKET INSIGHTS")
    print("=" * 60)
    
    insights = [
        "Healthcare communication training is a growing market driven by:",
        "  - Patient satisfaction scores tied to reimbursement (HCAHPS)",
        "  - Burnout reduction initiatives for healthcare workers",
        "  - Telehealth expansion requiring new communication skills",
        "  - AI adoption in healthcare creating need for human-AI collaboration training",
        "",
        "CareCompass differentiators:",
        "  - Real-time feedback vs. periodic training modules",
        "  - AI-powered analysis of actual patient conversations",
        "  - Continuous improvement vs. one-time certification",
        "  - Integrates with existing workflow (Plaud device)",
    ]
    
    for insight in insights:
        print(insight)
        results["market_insights"].append(insight)
    
    # Save results
    output_file = "market_research_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Full results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    main()
