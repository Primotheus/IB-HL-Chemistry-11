import random
import argparse
import matplotlib.pyplot as plt

MOVES = ["Rock", "Paper", "Scissors"]

def get_outcome(move_a, move_b):
    if move_a == move_b: return 0
    wins = {("Rock", "Scissors"), ("Scissors", "Paper"), ("Paper", "Rock")}
    return 1 if (move_a, move_b) in wins else -1

def play_rps():
    move_a, move_b = random.choice(MOVES), random.choice(MOVES)
    return move_a, move_b, get_outcome(move_a, move_b)

def plot_results(wallets, numbered, lettered):
    # Sort data for the graph
    sorted_wallets = dict(sorted(wallets.items(), key=lambda x: x[1], reverse=True))
    players = list(sorted_wallets.keys())
    balances = list(sorted_wallets.values())

    # Assign colors based on team
    colors = ['#3498db' if p in numbered else '#e74c3c' for p in players]

    plt.figure(figsize=(12, 6))
    bars = plt.bar(players, balances, color=colors)
    
    plt.axhline(0, color='black', linewidth=0.8)
    plt.ylabel('Yahu Funds ($)')
    plt.title('RPS Entropy Simulation')
    plt.ylim(0, max(balances) + 2)
    
    # Add labels on top of bars
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 0.2, yval, ha='center', va='bottom')

    plt.tight_layout()
    print("\n[Graph Generated] Close the plot window to finish the program.")
    plt.show()

def simulate(num_rounds: int, verbose: bool = True):
    # --- Setup ---
    numbered = [str(i) for i in range(1, 13)]   # ['1', '2', ..., '12']
    lettered = list("ABCDEFGHIJKL")             # ['A', 'B', ..., 'L']

    # Initial wallets set to integers since we deal in $1 increments
    wallets = {p: 1 for p in numbered + lettered}

    if verbose:
        print("=" * 65)
        print("   RPS Entropy Simulation")
        print("=" * 65)
        print(f"   Players: {', '.join(numbered)}  +  {', '.join(lettered)}")
        print(f"   Starting wallet: $1 each | Rounds: {num_rounds}")
        print("=" * 65)

    for round_num in range(num_rounds):
        # Matchmaking logic: rotation (skip bankrupt players when playing)
        matchups = []
        for i, letter in enumerate(lettered):
            num_idx = (i + round_num) % len(numbered)
            matchups.append((letter, numbered[num_idx]))

        round_results = []
        for letter, number in matchups:
            # CHECK BANKRUPTCY: Both players must have > $0
            if wallets[letter] <= 0 or wallets[number] <= 0:
                skipped = []
                if wallets[letter] <= 0:
                    skipped.append(letter)
                if wallets[number] <= 0:
                    skipped.append(number)
                reason = f"SKIPPED (Bankrupt: {' & '.join(skipped)})"
                round_results.append({
                    "letter": letter,
                    "number": number,
                    "move_letter": "-",
                    "move_number": "-",
                    "result": reason
                })
                continue

            # Play if both have funds
            move_l, move_n, outcome = play_rps()
            if outcome == 1:        # letter wins
                wallets[letter] += 1
                wallets[number] -= 1
                result = f"{letter} wins"
            elif outcome == -1:     # number wins
                wallets[number] += 1
                wallets[letter] -= 1
                result = f"{number} wins"
            else:
                result = "Draw"

            round_results.append({
                "letter": letter,
                "number": number,
                "move_letter": move_l,
                "move_number": move_n,
                "result": result,
            })

        if verbose:
            print(f"\n── Round {round_num + 1} (Offset +{round_num % len(numbered)}) ──")
            for r in round_results:
                print(f"  {r['letter']:>2} ({r['move_letter']:8}) vs {r['number']:>2} ({r['move_number']:8})  →  {r['result']}")

    plot_results(wallets, numbered, lettered)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rounds", type=int, default=15, help="Number of rounds")
    args = parser.parse_args()
    simulate(args.rounds)

if __name__ == "__main__":
    main()