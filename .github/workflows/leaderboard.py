#import ssl
import argparse
import json
import os
import urllib.request
from urllib.parse import urlencode

ITBENCH_API = os.getenv("ITBENCH_API")
ITBENCH_API_TOKEN = os.getenv("ITBENCH_API_TOKEN")
#ITBENCH_CERT = os.getenv("ITBENCH_CERT")


def get_leaderboard(benchmark_id: str = None, github_username: str = None):
    # Required as the current IT Bench server is not using a trusted certificate
    #ssl_context = ssl.create_default_context(cafile=ITBENCH_CERT)
    url = f"{ITBENCH_API}/gitops/aggregate-results"
    query_params = {}
    if benchmark_id is not None:
        query_params["benchmark_id"] = benchmark_id
    if github_username is not None:
        query_params["github_username"] = github_username
    if query_params:
        url += "?" + urlencode(query_params)
    headers = {
        "Authorization" : f"Bearer {ITBENCH_API_TOKEN}"
    }
    req = urllib.request.Request(url=url, headers=headers, method="GET")
    #res = urllib.request.urlopen(req, timeout=10, context=ssl_context) # Use this if using internal server
    res = urllib.request.urlopen(req, timeout=10)
    
    if res.getcode() != 200:
        print(f"Error requesting leaderboard JSON: {res.status_code}. {res.content}")
        exit(1)

    res_body = res.read()
    res_dict = json.loads(res_body.decode("utf-8"))
    return res_dict



def print_table(data):
    header_str = ['Rank', 'Agent Name', 'Overall Score', 'SRE', 'FinOps', 'CISO', 'Notes']
    line_fmt = '| {:^4} | {:^20} | {:^13} | {:^13} | {:^13} | {:^13} | {:<30} |'
    headers = line_fmt.format(*header_str)
    header_len = len(headers)
    print('-' * header_len)
    print(headers)
    print(line_fmt.format(*("---" * 7)))
    for bench_line in data:
        print(line_fmt.format(*bench_line))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Print IT Bench leaderboard")
    parser.add_argument("leaderboard")
    parser.add_argument("-u", "--github_username", type=str)
    parser.add_argument("-b", "--benchmark_id", type=str)
    args = parser.parse_args()
    if args.leaderboard =="global":
        leaderboard = leaderboard = get_leaderboard()
    else:
        leaderboard = get_leaderboard(args.benchmark_id, args.github_username)
   
    bench_summary = []
    [x.update({'pass_rate': int((x["num_of_passed"] / len(x["results"]))*100)}) for x in leaderboard]
    sorted(leaderboard, key=lambda x: x['pass_rate'])
    
    prev_score = None
    rank = 0
    count = 0
    for benchmark in leaderboard:
        #print(benchmark)
        count += 1
        if benchmark["pass_rate"] != prev_score:
            rank = count
        name = benchmark["agent"]
        score = f'{int(benchmark["pass_rate"] * 100)}%'
        agent_type = benchmark["agent_type"]
        checkmarks = "✅" * benchmark["num_of_passed"] if benchmark["num_of_passed"] > 0 else "N/A"
        notes = f'Related to {benchmark["incident_type"]} scenarios'

        sre = finops = ciso = "N/A"
        if agent_type == "SRE":
            sre = checkmarks
        elif agent_type == "FinOps":
            finops = checkmarks
        elif agent_type == "CISO":
            ciso = checkmarks
        bench_line = [
            rank,
            name,
            score,
            sre,
            finops,
            ciso,
            notes,
        ]

        prev_score = benchmark["pass_rate"]
        bench_summary.append(bench_line)


    print_table(bench_summary)