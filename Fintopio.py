# FINTOPIO BOT
# Author    : @fakinsit
# Date      : 30/08/24

import os
import time
import sys
import json
import re
import requests
from urllib.parse import unquote
from pyfiglet import Figlet
from colorama import Fore, Style
from onlylog import Log
from requests.exceptions import Timeout, ConnectionError

# Global API and Headers Configuration
API_BASE_URL = "https://fintopio-tg.fintopio.com/api"
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fintopio-tg.fintopio.com/",
    "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128", "Microsoft Edge WebView2";v="128"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "Windows",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Webapp": "true"
}

TOKEN_FILE = 'account_token.json'

# Display Banner
def banner():
    os.system("title FINTOPIO BOT" if os.name == "nt" else "clear")
    os.system("cls" if os.name == "nt" else "clear")
    custom_fig = Figlet(font='slant')
    print('')
    print(custom_fig.renderText(' FINTOPIO'))
    print(Fore.RED + '[#] [C] R E G E X    ' + Fore.GREEN + '[FINTOPIO BOT] $$ ' + Fore.RESET)
    print(Fore.GREEN + '[#] Welcome & Enjoy !', Fore.RESET)
    print(Fore.YELLOW + '[#] Having Troubles? PM Telegram [t.me/fakinsit] ', Fore.RESET)
    print('')

# Load tokens from the token file
def load_tokens():
    try:
        with open(TOKEN_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save tokens to the token file
def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as file:
        json.dump(tokens, file, indent=4)

# Check token validity
def is_token_valid(token):
    try:
        response = make_request('GET', '/fast/init', token=token)
        return response.status_code != 401
    except Exception as e:
        Log.error(f'[is_token_valid] Error checking token validity: {str(e)}')
        return False

# Get or refresh token for a user
def get_or_refresh_token(query_data, tokens):
    username = get_username(query_data)

    # Check if token already exists
    token = tokens.get(username)

    if token and is_token_valid(token):
        Log.success(f'Token for {Fore.YELLOW}@{username}{Fore.RESET} is still valid.')
        return token

    Log.warn(f'Token for {Fore.RESET}@{username}{Fore.RESET} is missing or expired. Generating a new token...')

    # Generate a new token
    new_token = get_login(query_data)
    if new_token:
        tokens[username] = new_token
        save_tokens(tokens)
        Log.success(f'New token for {Fore.YELLOW}@{username}{Fore.RESET} saved.')
        return new_token
    else:
        Log.error(f'Failed to get a new token for @{username}.')
        return None

# Function to send API requests with retries
def make_request(method, endpoint, token=None, payload=None, retries=3):
    url = f"{API_BASE_URL}{endpoint}"
    headers = HEADERS.copy()  # Create a copy of the global headers
    if token:
        headers["Authorization"] = f"Bearer {token}"

    session = requests.Session()

    for attempt in range(retries):
        try:
            if method == 'POST':
                response = session.post(url, headers=headers, json=payload)
            else:
                response = session.get(url, headers=headers)
            response.raise_for_status()
            return response
        except (Timeout, ConnectionError) as e:
            Log.error(f'[make_request] Network error: {str(e)}. Retrying...')
            time.sleep(2 ** attempt)  # Exponential backoff for retries
        except Exception as e:
            Log.error(f'[make_request] Error: {str(e)}')
            break
    return None

# Function to get login token
def get_login(query_data):
    try:
        response = make_request('GET', f"/auth/telegram?{query_data}")
        if response:
            token = response.json().get('token')
            Log.success(f'Login success{Fore.RESET}')
            return token
    except Exception as e:
        Log.error(f'[get_login] Error: {str(e)}')
    return None

# Function to extract username from query
def get_username(query_data):
    try:
        user_info = re.search('user=([^&]*)', query_data).group(1)
        decoded_user = unquote(user_info)
        user_obj = json.loads(decoded_user)
        username = user_obj.get('username', 'Unknown')
        return username
    except Exception as e:
        Log.error(f'[get_username] Error: {str(e)}')
    return "Unknown"

# Function to perform daily check-in
def check_in(token):
    try:
        r = make_request('GET', f"/referrals/data", token=token)
        jData = r.json()
        jsondaily = jData['isDailyRewardClaimed']
        if not jsondaily:
            Log.warn(f'{Fore.CYAN}daily reward not claimed yet{Fore.RESET}')
            Log.warn(f'{Fore.CYAN}claiming..{Fore.RESET}')
            try:
                response = make_request('POST', "/daily-checkins", token)
                if response:
                    data = response.json()
                    Log.warn(f'{Fore.CYAN}reward daily: {Fore.YELLOW}{data.get("dailyReward")}{Fore.RESET}')
                    Log.warn(f'{Fore.CYAN}total login day: {Fore.YELLOW}{data.get("totalDays")}{Fore.RESET}')
            except Exception as e:
                Log.error(f'[check_in] Error: {str(e)}')
        Log.warn(f'{Fore.CYAN}balance : {Fore.YELLOW}{jData["balance"]}{Fore.RESET}')
    except Exception as e:
        Log.error(f'[check_in] Error: {str(e)}')
        time.sleep(5)

# Function to handle asteroid (diamond clicker)
def nuke_asteroid(token, diamond_id, reward):
    try:
        payload = {"diamondNumber": diamond_id}
        response = make_request('POST', "/clicker/diamond/complete", token, payload)
        if response:
            Log.success(f'Asteroid crushed! Reward: {Fore.YELLOW}{reward}{Fore.RESET}')
        else:
            Log.error('[nuke_asteroid] Failed to claim reward')
    except Exception as e:
        Log.error(f'[nuke_asteroid] Error: {str(e)}')

# Function to start farming
def start_farming(token):
    try:
        response = make_request('POST', "/farming/farm", token)
        if response:
            Log.success(f'Farming started!{Fore.RESET}')
        else:
            Log.error('[start_farming] Failed to start farming')
    except Exception as e:
        Log.error(f'[start_farming] Error: {str(e)}')

# Function to claim farming rewards
def claim_farming(token):
    try:
        response = make_request('POST', "/farming/claim", token)
        if response:
            Log.success(f'Farming rewards claimed!{Fore.RESET}')
        else:
            Log.error('[claim_farming] Failed to claim farming rewards')
    except Exception as e:
        Log.error(f'[claim_farming] Error: {str(e)}')

# Function to handle tasks
def handle_tasks(token):
    try:
        response = make_request('GET', "/hold/tasks", token)
        if response:
            tasks = response.json().get('tasks', [])
            for task in tasks:
                if task['status'] == 'available':
                    start_task(token, task['id'], task['slug'])
                elif task['status'] == 'verified':
                    claim_task(token, task['id'], task['slug'], task['rewardAmount'])
    except Exception as e:
        Log.error(f'[handle_tasks] Error: {str(e)}')

# Start a task
def start_task(token, task_id, task_name):
    try:
        make_request('POST', f"/hold/tasks/{task_id}/start", token)
        Log.success(f'Task {Fore.YELLOW}{task_name}{Fore.CYAN} started!{Fore.RESET}')
    except Exception as e:
        Log.error(f'[start_task] Error: {str(e)}')

# Claim a completed task
def claim_task(token, task_id, task_name, reward_amount):
    try:
        response = make_request('POST', f"/hold/tasks/{task_id}/claim", token)
        if response and response.json().get('status') == 'completed':
            Log.success(f'Task {Fore.YELLOW}{task_name}{Fore.CYAN} claimed: {Fore.YELLOW}{reward_amount} points{Fore.RESET}')
    except Exception as e:
        Log.error(f'[claim_task] Error: {str(e)}')

# Main function to run tasks for all users
def run_bot():
    tokens = load_tokens()

    while True:  # Infinite loop to keep processing accounts in cycles
        with open('quentod.txt', 'r') as file:
            query_list = file.read().splitlines()

        for index, query_data in enumerate(query_list, start=1):
            username = get_username(query_data)
            success = False
            max_retries = 3  # Set the max number of retries per account

            for attempt in range(max_retries):
                try:
                    Log.success(f'{Fore.RESET}username: {Fore.YELLOW}@{username}{Fore.RESET}')
                    token = get_or_refresh_token(query_data, tokens)
                    if token:
                        check_in(token)
                        handle_tasks(token)
                        handle_asteroid_and_farming(token)
                        Log.success(f'Finished processing user: {Fore.YELLOW}@{username}{Fore.RESET}')
                        print('=' * 50)  # Line separator for clarity between users
                        sleep(60)  # Wait 60 seconds between actions
                        success = True
                        break  # If successful, break out of the retry loop
                    else:
                        raise ValueError(f"Failed to retrieve token for user: @{username}")
                except Exception as e:
                    Log.error(f"[run_bot] Error processing user @{username}: {str(e)}. Attempt {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        Log.warn(f'Retrying for user {Fore.YELLOW}@{username}{Fore.RESET}...')
                        time.sleep(2 ** attempt)  # Exponential backoff for retries
                    else:
                        Log.error(f"Max retries reached for user @{username}. Skipping to the next user.")

            if not success:
                Log.error(f"Skipping user: @{username} after {max_retries} attempts.")
                continue  # Proceed to the next user without restarting the process

        Log.success(f'{Fore.CYAN}All accounts processed. Restarting from account 1...{Fore.RESET}')

# Function to handle asteroid and farming logic
def handle_asteroid_and_farming(token):
    try:
        # Handle asteroid (diamond clicker)
        response = make_request('GET', "/clicker/diamond/state", token)
        if response:
            data = response.json()
            state = data['state']
            diamond_id = data.get('diamondNumber')
            reward = data['settings']['totalReward']
            if state == 'available':
                nuke_asteroid(token, diamond_id, reward)
            else:
                Log.warn(f'{Fore.CYAN}Asteroid state: {Fore.YELLOW}{state}{Fore.RESET}')
        
        # Handle farming
        response = make_request('GET', "/farming/state", token)
        if response:
            farm_state = response.json().get('state')
            if farm_state == 'idling':
                start_farming(token)
            elif farm_state == 'farmed':
                claim_farming(token)
            else:
                Log.warn(f'{Fore.CYAN}Farming state: {Fore.YELLOW}{farm_state}{Fore.RESET}')
    except Exception as e:
        Log.error(f'[handle_asteroid_and_farming] Error: {str(e)}')

def sleep(total_seconds):
    """Pause execution for `total_seconds` while printing remaining time in minutes, hours, seconds, and milliseconds."""
    
    start_time = time.time()
    end_time = start_time + total_seconds

    while True:
        current_time = time.time()
        remaining_time = end_time - current_time

        if remaining_time <= 0:
            print(f"{Fore.CYAN}Time's up!{Fore.RESET}                      ", end='\r') 
            break

        hours = int(remaining_time // 3600)
        minutes = int((remaining_time % 3600) // 60)
        seconds = int(remaining_time % 60)

        # Print the formatted time remaining
        time_remaining = f"{hours:02}:{minutes:02}:{seconds:02}"
        print(f"{Fore.RESET}[WAIT TIME: {Fore.YELLOW}{time_remaining}{Fore.CYAN}]{Fore.RESET}", end='\r')
        
        time.sleep(0.1)

# Main entry point
if __name__ == "__main__":
    try:
        banner()
        run_bot()
    except KeyboardInterrupt:
        sys.exit()
