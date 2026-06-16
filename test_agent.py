from agent.graph import run_agent

response, logs = run_agent("I want to return my order")
print("Response:", response)
print("\nLogs:")
for log in logs:
    print(log)