import sys
import hmac
import hashlib
import secrets
from typing import List, Tuple
from tabulate import tabulate
import numpy as np
from colorama import Fore, Style


class ProbabilityCalculator:
    @staticmethod
    def calculate_probabilities(dice):
        num_dice = len(dice)
        probabilities = np.zeros((num_dice, num_dice))

        for i in range(num_dice):
            for j in range(num_dice):
                if i == j:
                    probabilities[i][j] = 0.3333  # Ties have ~33% probability
                else:
                    probabilities[i][j] = ProbabilityCalculator.compare_dice(dice[i], dice[j])

        return probabilities

    @staticmethod
    def compare_dice(dice_a, dice_b):
        """Simulate all possible outcomes and calculate the win probability for dice_a."""
        win_count = 0
        total_count = 0
        for face_a in dice_a.values:
            for face_b in dice_b.values:
                if face_a > face_b:
                    win_count += 1
                total_count += 1
        return round(win_count / total_count, 4)

    @staticmethod
    def colorize_probability(value):
        """Colorize probabilities based on their value."""
        if value > 0.5:
            return f"{Fore.GREEN}{value:.4f}{Style.RESET_ALL}"  # Green for high probabilities
        elif value >= 0.33:
            return f"{Fore.YELLOW}{value:.4f}{Style.RESET_ALL}"  # Yellow for medium probabilities
        else:
            return f"{Fore.RED}{value:.4f}{Style.RESET_ALL}"  # Red for low probabilities

    @staticmethod
    def generate_help_table(dice):
        probabilities = ProbabilityCalculator.calculate_probabilities(dice)
        headers = ["User dice v"] + [",".join(map(str, d.values)) for d in dice]

        rows = []
        for i, dice_row in enumerate(dice):
            row = [",".join(map(str, dice_row.values))]
            for j in range(len(dice)):
                if i == j:
                    row.append(f"{Fore.CYAN}- (0.3333){Style.RESET_ALL}")  # Cyan for ties
                else:
                    row.append(ProbabilityCalculator.colorize_probability(probabilities[i][j]))
            rows.append(row)

        table = tabulate(rows, headers, tablefmt="grid")
        return table


class Dice:
    def __init__(self, values: List[int]):
        if len(values) != 6:
            raise ValueError("Each die must have exactly 6 values.")
        self.values = values

    def roll(self, index: int) -> int:
        return self.values[index]


class DiceParser:
    @staticmethod
    def parse(args: List[str]) -> List[Dice]:
        if len(args) < 3:
            raise ValueError("At least 3 dice configurations are required.")
        dice = []
        for arg in args:
            try:
                values = list(map(int, arg.split(',')))
                dice.append(Dice(values))
            except ValueError:
                raise ValueError(f"Invalid dice configuration: {arg}")
        return dice


class FairRandomGenerator:
    @staticmethod
    def generate_fair_number(min_val: int, max_val: int) -> Tuple[int, str, bytes]:
        """Generates a fair number, HMAC, and secret key."""
        secret_key = secrets.token_bytes(32)  # Generate a 256-bit key
        computer_number = secrets.randbelow(max_val - min_val + 1) + min_val
        hmac_value = hmac.new(secret_key, str(computer_number).encode(), hashlib.sha3_256).hexdigest()
        return computer_number, hmac_value, secret_key


class Game:
    def __init__(self, dice: List[Dice]):
        self.dice = dice
        self.remaining_dice = list(range(len(dice)))  # Track indices of remaining dice

    def determine_first_move(self) -> str:
        print("\nLet's determine who makes the first move.")
        computer_number, hmac_value, secret_key = FairRandomGenerator.generate_fair_number(0, 1)
        print(f"I selected a random value in the range 0..1 (HMAC={hmac_value}).")
        print("Try to guess my selection.")
        user_guess = input("0 - 0\n1 - 1\nX - exit\n? - help\nYour selection: ").strip()

        if user_guess.lower() == "x":
            print("Exiting the game.")
            sys.exit(0)
        elif user_guess.lower() == "?":
            self.help_option()
            return self.determine_first_move()

        try:
            user_guess = int(user_guess)
            if user_guess not in [0, 1]:
                raise ValueError
        except ValueError:
            print("Invalid input. Please choose 0 or 1.")
            return self.determine_first_move()

        print(f"My selection: {computer_number} (KEY={secret_key.hex()}).")
        return "computer" if computer_number != user_guess else "user"

    def computer_select_dice(self, is_first: bool) -> Tuple[Dice, int]:
        computer_choice = self.remaining_dice.pop(0)  # Automatically select the first available die
        computer_dice = self.dice[computer_choice]
        if not is_first:
            print(f"I choose the [{','.join(map(str, computer_dice.values))}] dice.")
        return computer_dice, computer_choice

    def user_select_dice(self) -> Tuple[Dice, int]:
        print("\nChoose your dice:")
        for i in self.remaining_dice:
            print(f"{i} - {','.join(map(str, self.dice[i].values))}")
        print("X - exit")
        print("? - help")

        selection = input("Your selection: ").strip()
        if selection.lower() == "x":
            print("Exiting the game.")
            sys.exit(0)
        elif selection.lower() == "?":
            self.help_option()
            return self.user_select_dice()
        print(f"You choose the {self.dice[int(selection)].values} dice.")
        try:
            index = int(selection)
            if index in self.remaining_dice:
                self.remaining_dice.remove(index)  # Remove selected die from remaining dice
                return self.dice[index], index
        except ValueError:
            pass

        print("Invalid choice. Try again.")
        return self.user_select_dice()

    def play_throw(self, dice: Dice, is_user: bool):
        if is_user:
            print("\nIt's time for your throw.")
        else:
            print("\nIt's time for my throw.")

        computer_number, hmac_value, secret_key = FairRandomGenerator.generate_fair_number(0, 5)
        print(f"I selected a random value in the range 0..5 (HMAC={hmac_value}).")

        user_number = input("Add your number modulo 6.\n0 - 0\n1 - 1\n2 - 2\n3 - 3\n4 - 4\n5 - 5\nX - exit\n? - help\nYour selection: ").strip()
        if user_number.lower() == "x":
            print("Exiting the game.")
            sys.exit(0)
        elif user_number.lower() == "?":
            self.help_option()
            return self.play_throw(dice, is_user)

        try:
            user_number = int(user_number)
            if 0 <= user_number <= 5:
                result = (computer_number + user_number) % 6
                print(f"My number is {computer_number} (KEY={secret_key.hex()}).")
                print(f"The result is {computer_number} + {user_number} = {result} (mod 6).")
                return dice.roll(result)
        except ValueError:
            pass

        print("Invalid input. Try again.")
        return self.play_throw(dice, is_user)

    def start_game(self):
        first_mover = self.determine_first_move()

        if first_mover == "computer":
            computer_dice, _ = self.computer_select_dice(is_first=True)
            print(f"I make the first move and choose the {computer_dice.values} dice.")
            user_dice, _ = self.user_select_dice()
        else:
            print("You make the first move.")
            user_dice, _ = self.user_select_dice()
            computer_dice, _ = self.computer_select_dice(is_first=False)

        computer_throw = self.play_throw(computer_dice, is_user=False)
        print(f"My throw is {computer_throw}.")
        user_throw = self.play_throw(user_dice, is_user=True)
        print(f"Your throw is {user_throw}.")

        if user_throw > computer_throw:
            print(f"You win ({user_throw} > {computer_throw})!")
        elif user_throw < computer_throw:
            print(f"I win ({computer_throw} > {user_throw})!")
        else:
            print(f"It's a tie ({user_throw} = {computer_throw})!")

    def help_option(self):
        print("\nGame Rules:")
        print("Each dice has six faces with values as defined at the start.")
        print("Your goal is to choose a dice with a higher probability of winning.")
        print("\nProbability of the win for the user:")

        table = ProbabilityCalculator.generate_help_table(self.dice)
        print(table)


def main():
    if len(sys.argv) < 2:
        print("Usage: python game.py <dice_configurations>")
        print("Example: python game.py 2,2,4,4,9,9 6,8,1,1,8,6 7,5,3,7,5,3")
        return

    try:
        dice = DiceParser.parse(sys.argv[1:])
        game = Game(dice)
        game.start_game()
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()