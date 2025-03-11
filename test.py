import re

# List of phone numbers
phone_numbers = [
    "01017643878", "01018164656", "01119918122", "01222160736",
    "+923032210657", "+639051067626", "00823174297579", "+639087651766",
    "18764795618", "+20 101 600 9521", "01099255789", "01066972918",
    "07034285759", "00201156640881", "01097524550", "01060718467",
    "+201012428532", "12687704063", "01152527214", "01205856139",
    "+201033507698", "01013271566", "09776496089", "09194144114",
    "+63 963 984 3342", "08134498982", "+2348051143134", "01226780542",
    "+918698358751", "+201017369878"
]

# Function to format phone numbers
def format_phone_number(number):
    # Remove spaces, dashes, and parentheses
    number = re.sub(r'[^\d+]', '', number)
    
    # Check if it's already in international format
    if number.startswith("+") and not number.startswith("+20"):
        return number  # Foreign number, do nothing
    
    # Remove leading zeros, country codes, or '00' international prefixes
    number = re.sub(r'^(00|0+20|0+)', '', number)

    # Prepend +20 to numbers that aren't already formatted
    if not number.startswith("+"):
        return "+20" + number
    return number


# Process and format the numbers
formatted_numbers = [format_phone_number(num) for num in phone_numbers]

# Output results
for num in formatted_numbers:
    print(num)
