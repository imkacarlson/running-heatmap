#!/usr/bin/env python3
"""
Simple dynamic profile analyzer - truly evidence-based recommendations
"""
import pstats
import sys
import re
from pathlib import Path

def find_sleep_calls():
    """Find sleep calls in source code."""
    sleep_calls = []
    for py_file in Path(__file__).parent.glob("*.py"):
        if py_file.name == Path(__file__).name:
            continue
        try:
            with open(py_file, 'r') as f:
                lines = f.readlines()
            for line_num, line in enumerate(lines, 1):
                if 'sleep(' in line and not line.strip().startswith('#'):
                    match = re.search(r'sleep\(([^)]+)\)', line)
                    duration = match.group(1) if match else "unknown"
                    sleep_calls.append({
                        'file': py_file.name,
                        'line': line_num,
                        'duration': duration,
                        'code': line.strip()
                    })
        except:
            continue
    return sleep_calls

def analyze_profile(prof_file_path=None):
    """Analyze profile with truly dynamic recommendations."""
    
    # Find profile file
    if prof_file_path:
        prof_file = Path(prof_file_path)
    else:
        prof_file = Path(__file__).parent / "prof" / "combined.prof"
    
    if not prof_file.exists():
        print(f"❌ Profile file not found: {prof_file}")
        return
    
    print(f"🔍 Dynamic Profile Analysis: {prof_file.name}")
    print("=" * 50)
    
    # Load profile and extract key data points
    stats = pstats.Stats(str(prof_file))
    
    # Get the raw stats data by examining the underlying object
    # This is a bit hacky but works with pstats internal structure
    stats_dict = stats.stats
    
    # Calculate totals and categorize
    sleep_time = 0
    network_time = 0
    poll_time = 0
    user_code_time = 0
    total_calls = 0
    
    top_functions = []
    
    for (filename, line, func_name), (cc, nc, tt, ct, callers) in stats_dict.items():
        func_info = f"{filename}:{line}({func_name})"
        top_functions.append((tt, func_info))
        
        if 'time.sleep' in func_info:
            sleep_time += tt
        elif any(net in func_info.lower() for net in ['recv_into', 'socket', 'urllib', 'http']):
            network_time += tt
        elif 'poll' in func_info.lower():
            poll_time += tt
        elif re.search(r'/test_.*\.py:', func_info) and tt > 0.05:
            user_code_time += tt
        
        total_calls += cc if isinstance(cc, int) else 1
    
    # Sort top functions by time
    top_functions.sort(reverse=True)
    
    # Calculate total time from the top-level function
    total_time = max(ct for _, (_, _, _, ct, _) in stats_dict.items())
    
    print(f"📊 Total Execution Time: {total_time:.1f}s")
    print(f"🔢 Total Function Calls: {total_calls:,}")
    print()
    
    # Show top time consumers
    print("⏱️  TOP TIME CONSUMERS:")
    print("-" * 30)
    for i, (tt, func_info) in enumerate(top_functions[:8], 1):
        percentage = (tt / total_time * 100) if total_time > 0 else 0
        print(f"{i}. {tt:6.2f}s ({percentage:4.1f}%) - {func_info[:60]}")
    
    print()
    
    # DYNAMIC RECOMMENDATIONS - Only based on actual findings
    recommendations = []
    
    # Sleep analysis - only if significant
    if sleep_time > 1 or (sleep_time / total_time > 0.03):
        sleep_percentage = (sleep_time / total_time * 100) if total_time > 0 else 0
        priority = "🚨 HIGH PRIORITY" if sleep_percentage > 15 else "⚠️  MEDIUM PRIORITY"
        
        recommendations.append({
            'priority': priority,
            'finding': f"Sleep calls consume {sleep_time:.1f}s ({sleep_percentage:.1f}% of total)",
            'action': "Replace sleep() calls with WebDriverWait conditions",
            'impact': f"Potential savings: {sleep_time * 0.6:.1f}s"
        })
        
        # Find actual sleep calls in code
        source_sleeps = find_sleep_calls()
        if source_sleeps:
            long_sleeps = [s for s in source_sleeps if s['duration'].replace('.', '').isdigit() and float(s['duration']) >= 5]
            if long_sleeps:
                recommendations.append({
                    'priority': "🚨 HIGH PRIORITY",
                    'finding': f"{len(long_sleeps)} sleep calls ≥5 seconds found",
                    'action': "Focus on long sleep calls first",
                    'impact': "Major execution time reduction possible"
                })
    
    # User code analysis - only if taking significant time
    if user_code_time > 0.5:
        recommendations.append({
            'priority': "⚠️  MEDIUM PRIORITY", 
            'finding': f"User test functions consume {user_code_time:.1f}s total",
            'action': "Profile individual slow test functions",
            'impact': f"Potential optimization in test logic"
        })
    
    # Polling analysis - only if excessive
    if poll_time > 1 or (poll_time / total_time > 0.02):
        poll_percentage = (poll_time / total_time * 100) if total_time > 0 else 0
        recommendations.append({
            'priority': "⚠️  MEDIUM PRIORITY",
            'finding': f"Polling operations consume {poll_time:.1f}s ({poll_percentage:.1f}%)",
            'action': "Review WebDriverWait strategies and timeouts", 
            'impact': "Better test stability and performance"
        })
    
    # Network analysis - only flag if abnormal
    if network_time > 0 and (network_time / total_time > 0.9):
        recommendations.append({
            'priority': "📋 LOW PRIORITY",
            'finding': f"Network I/O dominates execution ({network_time/total_time*100:.1f}%)",
            'action': "Check network connectivity and WebDriver config",
            'impact': "Infrastructure optimization"
        })
    
    # SHOW RESULTS
    if recommendations:
        print("🎯 PERFORMANCE ISSUES DETECTED:")
        print("-" * 40)
        
        for rec in recommendations:
            print(f"{rec['priority']}: {rec['finding']}")
            print(f"   → {rec['action']}")
            print(f"   💡 {rec['impact']}")
            print()
        
        # Show sleep call locations if relevant
        if any('sleep' in rec['finding'].lower() for rec in recommendations):
            source_sleeps = find_sleep_calls()
            if source_sleeps:
                print("📍 SLEEP CALLS IN SOURCE:")
                print("-" * 30)
                by_file = {}
                for call in source_sleeps:
                    if call['file'] not in by_file:
                        by_file[call['file']] = []
                    by_file[call['file']].append(call)
                
                for file_name, calls in by_file.items():
                    print(f"\n{file_name}:")
                    for call in calls:
                        print(f"  Line {call['line']:3}: sleep({call['duration']}) - {call['code'][:50]}")
    
    else:
        print("✅ NO SIGNIFICANT PERFORMANCE ISSUES DETECTED!")
        print("🎉 Your code is running efficiently.")
        print()
        
        # Still show basic info for context
        if sleep_time > 0:
            sleep_pct = (sleep_time / total_time * 100) if total_time > 0 else 0
            print(f"📊 Sleep calls: {sleep_time:.1f}s ({sleep_pct:.1f}%) - within acceptable range")
        
        if network_time > 0:
            net_pct = (network_time / total_time * 100) if total_time > 0 else 0 
            print(f"🌐 Network I/O: {network_time:.1f}s ({net_pct:.1f}%) - normal for WebDriver tests")

if __name__ == '__main__':
    prof_path = sys.argv[1] if len(sys.argv) > 1 else None
    analyze_profile(prof_path)