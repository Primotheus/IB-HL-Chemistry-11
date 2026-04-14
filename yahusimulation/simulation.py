"""
Rock Paper Scissors Tournament Simulation
==========================================
24 players: 12 numbered (1-12) and 12 lettered (A-L)
Each round, lettered players rotate by one position to face a new numbered opponent.
Winner takes $1 from loser.
NEW RULE: Players with $0 are 'bankrupt' and cannot participate in matches.
"""

import random
import argparse
from collections import defaultdict

MOVES = ["Rock", "Paper", "Scissors"]


def get_outcome(move_a, move_b):
    """Returns: 1 if a wins, -1 if b wins, 0 if draw."""
    if move_a == move_b:
        return 0
    wins = {("Rock", "Scissors"), ("Scissors", "Paper"), ("Paper", "Rock")}
    return 1 if (move_a, move_b) in wins else -1


def play_rps():
    """Returns (move_a, move_b, outcome)."""
    move_a = random.choice(MOVES)
    move_b = random.choice(MOVES)
    return move_a, move_b, get_outcome(move_a, move_b)


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

    # --- Final standings ---
    if verbose:
        print("\n" + "=" * 65)
        print("   FINAL STANDINGS")
        print("=" * 65)

        all_players = sorted(wallets.items(), key=lambda x: -x[1])
        for rank, (player, amount) in enumerate(all_players, 1):
            label = "Num" if player.isdigit() else "Let"
            bar = "█" * max(0, int(amount))
            status = " [poor]" if amount <= 0 else ""
            print(f"  #{rank:>2}  {player:>2} ({label})  ${amount:>2}  {bar}{status}")

        # Group stats
        num_total = sum(wallets[p] for p in numbered)
        let_total = sum(wallets[p] for p in lettered)
        print(f"\n  Team Totals: Numbers ${num_total} | Letters ${let_total}")
        print("=" * 65)

    return wallets


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rounds", type=int, default=12)
    parser.add_argument("-q", "--quiet", action="store_true")
    args = parser.parse_args()

    simulate(args.rounds, verbose=not args.quiet)


if __name__ == "__main__":
    main()
