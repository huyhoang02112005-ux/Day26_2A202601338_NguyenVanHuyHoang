from server import search_logs, get_error_summary

if __name__ == "__main__":
    print("--- 1. Testing get_error_summary() ---")
    summary = get_error_summary()
    print("Summary Result:", summary)

    print("\n--- 2. Testing search_logs(keyword='timeout', log_level='ERROR') ---")
    logs = search_logs(keyword="timeout", log_level="ERROR", limit=5)
    for log in logs:
        print("  -", log)

    print("\n--- 3. Testing search_logs(log_level='CRITICAL') ---")
    critical_logs = search_logs(log_level="CRITICAL")
    for log in critical_logs:
        print("  -", log)
