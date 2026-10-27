import datetime

def main():
    # TODO: load last 24h data from Firebase/BigQuery
    # TODO: run simulations
    # TODO: write results back
    now = datetime.datetime.utcnow().isoformat()
    print(f"Simulation job ran at {now}")

if __name__ == "__main__":
    main()
