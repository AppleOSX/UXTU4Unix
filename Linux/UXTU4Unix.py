import os, time, subprocess, getpass, webbrowser, logging, sys, binascii
import urllib.request, json, select
from configparser import ConfigParser

LOCAL_VERSION = "0.2.9"
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Unix/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/AppleOSX/UXTU4Unix/releases/latest"
cpu_codename = ["Raven", "Picasso", "Massite", "Renoir", "Cezanne", "Dali", "Lucienne", "Van Gogh", "Rembrandt", "Phoenix Point", "Hawk Point", "Strix Point"]
os.makedirs('Logs', exist_ok=True)
logging.basicConfig(filename='Logs/UXTU4Unix.log', filemode='w', encoding='utf-8',
                    level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler())
current_dir = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = f'{current_dir}/Assets/config.ini'
cfg = ConfigParser()
cfg.read(CONFIG_PATH)

def clear():
    subprocess.call('clear', shell=True)
    logging.info(r"""
   _   ___  _______ _   _ _ _  _   _      _     
  | | | \ \/ /_   _| | | | | || | | |_ _ (_)_ __
  | |_| |>  <  | | | |_| |_  _| |_| | ' \| \ \ /
   \___//_/\_\ |_|  \___/  |_| \___/|_||_|_/_\_\ """)
    logging.info("")
    command = "grep -m 1 'model name' /proc/cpuinfo | awk -F ': ' '{print $2}'"
    logging.info(f'  {get_hardware_info(command)}')
    if cfg.get('Settings', 'Debug', fallback='0') == '1':
        logging.info(f"  Loaded: {cfg.get('User', 'Preset',fallback = '')}")
    logging.info(f"  Version: {LOCAL_VERSION} by GorouFlex and AppleOSX (Linux Edition)")
    logging.info("")
    
def get_hardware_info(command, use_sudo=False):
    password = cfg.get('User', 'Password', fallback='')
    if use_sudo:
        command = f"sudo -S {command}"
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output, error = process.communicate(input=password.encode())
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        output, error = process.communicate()
    return output.decode('utf-8').strip()

def get_presets():
    command = f"{current_dir}/Assets/ryzenadj -i | grep 'CPU Family' | awk -F': ' '{{print $2}}'"
    cpu_family = get_hardware_info(command, use_sudo=True)
    cpu_model = get_hardware_info("cat /proc/cpuinfo | grep 'model name' | head -1 | awk -F': ' '{print $2}'")
    loca = None
    try:
        if cpu_codename.index(cpu_family) < cpu_codename.index("Massite"):
            if "U" in cpu_model or "e" in cpu_model or "Ce" in cpu_model:
                loca = "Assets.Presets.AMDAPUPreMatisse_U_e_Ce"
                from Assets.Presets.AMDAPUPreMatisse_U_e_Ce import PRESETS
            elif "H" in cpu_model:
                loca = "Assets.Presets.AMDAPUPreMatisse_H"
                from Assets.Presets.AMDAPUPreMatisse_H import PRESETS
            elif "GE" in cpu_model:
                loca = "Assets.Presets.AMDAPUPreMatisse_GE"
                from Assets.Presets.AMDAPUPreMatisse_GE import PRESETS
            elif "G" in cpu_model:
                loca = "Assets.Presets.AMDAPUPreMatisse_G"
                from Assets.Presets.AMDAPUPreMatisse_G import PRESETS
            else:
                loca = "Assets.Presets.AMDCPU"
                from Assets.Presets.AMDCPU import PRESETS
        elif cpu_codename.index(cpu_family) > cpu_codename.index("Massite"):
            if "U" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_U"
                from Assets.Presets.AMDAPUPostMatisse_U import PRESETS
            elif "HX" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_HX"
                from Assets.Presets.AMDAPUPostMatisse_HX import PRESETS
            elif "HS" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_HS"
                from Assets.Presets.AMDAPUPostMatisse_HS import PRESETS
            elif "H" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_H"
                from Assets.Presets.AMDAPUPostMatisse_H import PRESETS
            elif "G" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_G"
                from Assets.Presets.AMDAPUPostMatisse_G import PRESETS
            elif "GE" in cpu_model:
                loca = "Assets.Presets.AMDAPUPostMatisse_GE"
                from Assets.Presets.AMDAPUPostMatisse_GE import PRESETS
            else:
                loca = "Assets.Presets.AMDCPU"
                from Assets.Presets.AMDCPU import PRESETS
    except:  
        loca = "Assets.Presets.AMDCPU"
        from Assets.Presets.AMDCPU import PRESETS
    cfg.set('User', 'Preset', loca)
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    return PRESETS

def welcome_tutorial():
    if not cfg.has_section('User'):
        cfg.add_section('User')
    if not cfg.has_section('Settings'):
        cfg.add_section('Settings')
    clear()
    logging.info("--------------- Welcome to UXTU4Unix ---------------")
    logging.info("Designed for AMD Zen-based processors on macOS/Linux")
    logging.info("Based on RyzenAdj and inspired by UXTU")
    logging.info("Let's get started with some initial setup ~~~")
    input("Press Enter to continue...")
    clear()
    while True:
        subprocess.run("sudo -k", shell=True)
        password = getpass.getpass("Enter your sudo (login) password: ")
        sudo_check_command = f"echo '{password}' | sudo -S ls /"
        sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if sudo_check_process.returncode == 0:
            break
        else:
            logging.info("Incorrect sudo password. Please try again.")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    try:
        cfg.set('User', 'Password', password)
        cfg.set('Settings', 'Time', '30')
        cfg.set('Settings', 'SoftwareUpdate', '1')
        cfg.set('Settings', 'ReApply', '0')
        cfg.set('Settings', 'ApplyOnStart', '1')
        cfg.set('Settings', 'DynamicMode', '0')
        cfg.set('Settings', 'Debug', '1')
    except ValueError:
        logging.info("Invalid option.")
        raise SystemExit
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    preset_cfg()
    clear()
       
def settings():
    options = {
        "1": preset_cfg,
        "2": sleep_cfg,
        "3": dynamic_cfg,
        "4": reapply_cfg,
        "5": applystart_cfg,
        "6": cfu_cfg,
        "7": pass_cfg,
        "8": debug_cfg,
        "r": reset,
        "b": "break"
    }
    while True:
        clear()
        logging.info("--------------- Settings ---------------")
        logging.info("1. Preset\n2. Sleep time")
        logging.info("3. Dynamic mode\n4. Auto reapply")
        logging.info("5. Apply on start")
        logging.info("6. Software update")
        logging.info("7. Sudo password")
        logging.info("8. Debug\n")
        logging.info("R. Reset all saved settings")
        logging.info("B. Back")
        settings_choice = input("Option: ").lower().strip()
        action = options.get(settings_choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def applystart_cfg():
    while True:
        clear()
        logging.info("--------------- Apply on start ---------------")
        logging.info("(Apply preset when start)")
        start_enabled = cfg.get('Settings', 'ApplyOnStart', fallback='1') == '1'
        logging.info("Status: Enabled" if start_enabled else "Status: Disabled")
        logging.info("\n1. Enable Apply on start\n2. Disable Apply on start")
        logging.info("\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'ApplyOnStart', '1')
        elif choice == "2":
            cfg.set('Settings', 'ApplyOnStart', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def debug_cfg():
    while True:
        clear()
        logging.info("--------------- Debug ---------------")
        logging.info("(Display some process information)")
        debug_enabled = cfg.get('Settings', 'Debug', fallback='1') == '1'
        logging.info("Status: Enabled" if debug_enabled else "Status: Disabled")
        logging.info("\n1. Enable Debug\n2. Disable Debug")
        logging.info("\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'Debug', '1')
        elif choice == "2":
            cfg.set('Settings', 'Debug', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def reapply_cfg():
    while True:
        clear()
        logging.info("--------------- Auto reapply ---------------")
        logging.info("(Automatic reapply preset)")
        reapply_enabled = cfg.get('Settings', 'ReApply', fallback='0') == '1'
        logging.info("Status: Enabled" if reapply_enabled else "Status: Disabled")
        logging.info("\n1. Enable Auto reapply\n2. Disable Auto reapply")
        logging.info("\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'ReApply', '1')
        elif choice == "2":
            cfg.set('Settings', 'ReApply', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
                        
def dynamic_cfg():
    while True:
        clear()
        dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'
        logging.info("--------------- Dynamic mode ---------------")
        logging.info("(Automatic switch preset based on your battery usage)")
        logging.info("Status: Enabled" if dm_enabled else "Status: Disabled")
        logging.info("\n1. Enable Dynamic Mode\n2. Disable Dynamic Mode\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'DynamicMode', '1')
        elif choice == "2":
            cfg.set('Settings', 'DynamicMode', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def sleep_cfg():
    while True:
        clear()
        time = cfg.get('Settings', 'Time', fallback='30')
        logging.info("--------------- Sleep time ---------------")
        logging.info(f"Auto reapply every: {time} seconds")
        logging.info("\n1. Change\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            set_time = input("Enter your auto reapply time (Default is 30s): ")
            cfg.set('Settings', 'Time', set_time)
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")

def pass_cfg():
    while True:
        clear()
        pswd = cfg.get('User', 'Password', fallback='')
        logging.info("--------------- Sudo password ---------------")
        logging.info(f"Current sudo (login) password: {pswd}")
        logging.info("\n1. Change password\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            while True:
                subprocess.run("sudo -k", shell=True)
                password = getpass.getpass("Enter your sudo (login) password: ")
                sudo_check_command = f"echo '{password}' | sudo -S ls /"
                sudo_check_process = subprocess.run(sudo_check_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if sudo_check_process.returncode == 0:
                    cfg.set('User', 'Password', password)
                    with open(CONFIG_PATH, 'w') as config_file:
                        cfg.write(config_file)
                    break
                else:
                    logging.info("Incorrect sudo password. Please try again.")
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")

def cfu_cfg():
    while True:
        clear()
        cfu_enabled = cfg.get('Settings', 'SoftwareUpdate', fallback='1') == '1'
        logging.info("--------------- Software update ---------------")
        logging.info(f"Status: {'Enabled' if cfu_enabled else 'Disabled'}")
        logging.info("\n1. Enable Software update\n2. Disable Software update\n\nB. Back")
        choice = input("Option: ").strip()
        if choice == "1":
            cfg.set('Settings', 'SoftwareUpdate', '1')
        elif choice == "2":
            cfg.set('Settings', 'SoftwareUpdate', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue.")
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def preset_cfg():
    PRESETS = get_presets()
    while True:
        clear()
        logging.info("--------------- Preset ---------------")
        for i, (preset_name, preset_value) in enumerate(PRESETS.items(), start=1):
            logging.info(f"{i}. {preset_name}")
        logging.info("\nD. Dynamic Mode")
        logging.info("C. Custom (Beta)")
        logging.info("B. Back")
        logging.info("We recommend using the Dynamic Mode for normal tasks and better power management")
        choice = input("Option: ").lower().strip()
        if choice == 'c':
            custom_args = input("Enter your custom arguments: ")
            cfg.set('User', 'Mode', 'Custom')
            cfg.set('User', 'CustomArgs', custom_args)
            logging.info("Set preset successfully!")
            input("Press Enter to continue...")
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
            break
        elif choice == 'd':
            cfg.set('User', 'Mode', 'Balance')
            cfg.set('Settings', 'DynamicMode', '1')
            cfg.set('Settings', 'ReApply', '1')
            logging.info("Set preset successfully!")
            input("Press Enter to continue...")
            with open(CONFIG_PATH, 'w') as config_file:
                cfg.write(config_file)
            break
        elif choice == 'b':
            return
        else:
            try:
                preset_number = int(choice)
                preset_name = list(PRESETS.keys())[preset_number - 1]
                cfg.set('User', 'Mode', preset_name)
                logging.info("Set preset successfully!")
                input("Press Enter to continue...")
                with open(CONFIG_PATH, 'w') as config_file:
                    cfg.write(config_file)
                break
            except ValueError:
                logging.info("Invalid option.")
                input("Press Enter to continue")

def reset():
    os.remove(CONFIG_PATH)
    welcome_tutorial()
    
def read_cfg() -> str:
    return cfg.get('User', 'Mode', fallback='')

def check_cfg_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        welcome_tutorial()
        return
    required_keys_user = ['password', 'mode']
    required_keys_settings = ['time', 'dynamicmode', 'reapply', 'applyonstart', 'softwareupdate', 'debug']
    if not cfg.has_section('User') or not cfg.has_section('Settings') or \
    any(key not in cfg['User'] for key in required_keys_user) or \
    any(key not in cfg['Settings'] for key in required_keys_settings):
      reset()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def get_changelog():
    request = urllib.request.Request(GITHUB_API_URL)
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data['body']

def updater():
    clear()
    changelog = get_changelog()
    logging.info("--------------- UXTU4Unix Software Update ---------------")
    logging.info("A new update is available!")
    logging.info(
        f"Changelog for the latest version ({get_latest_ver()}):\n{changelog}"
    )
    logging.info("Do you want to update? (y/n): ")
    choice = input("Option: ").lower().strip()
    if choice == "y":
        subprocess.run(["python3", f"{current_dir}/Assets/SU.py"])
        logging.info("Updating...")
        logging.info("Update complete. Restarting the application, please close this window...")
    elif choice == "n":
        logging.info("Skipping update...")
    else:
        logging.info("Invalid option.")
    raise SystemExit

def check_updates():
    clear()
    max_retries = 10
    skip_update_check = False
    for i in range(max_retries):
        try:
            latest_version = get_latest_ver()
        except:
            if i < max_retries - 1:
                logging.info(f"Failed to fetch latest version. Retrying {i+1}/{max_retries}...")
                time.sleep(5)
            else:
                result = input("Do you want to skip the check for updates? (y/n): ").lower().strip()
                if result == "y":
                    skip_update_check = True
                else:
                    logging.info("Quitting...")
                    raise SystemExit
    if not skip_update_check and LOCAL_VERSION < latest_version:
        updater()

def about():
    options = {
        "1": lambda: webbrowser.open("https://www.github.com/AppleOSX/UXTU4Unix"),
        "f": updater,
        "b": "break"
    }
    while True:
        clear()
        logging.info("About UXTU4Unix")
        logging.info("The L2T Update (2FUTURE)")
        logging.info("----------------------------")
        logging.info("Maintainer: GorouFlex\nCLI: GorouFlex")
        logging.info("GUI: NotchApple1703\nAdvisor: NotchApple1703")
        logging.info("Command file: CorpNewt\nTester: nlqanh524")
        logging.info("----------------------------")
        try:
          logging.info(f"F. Force update to the latest version ({get_latest_ver()})")
        except:
           pass
        logging.info("\nB. Back")
        choice = input("Option: ").lower().strip()
        action = options.get(choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def preset_menu():
    PRESETS = get_presets()
    clear()
    logging.info("Apply power management settings:")
    logging.info("1. Load saved settings from config file\n2. Load from available premade preset\n\nD. Dynamic Mode")
    logging.info("B. Back")
    preset_choice = input("Option: ").strip()
    if preset_choice == "1":
        if user_mode := read_cfg():
            if user_mode in PRESETS:
                apply_smu(PRESETS[user_mode], user_mode)
            else:
                apply_smu(user_mode, user_mode)
        else:
            logging.info("Config file is missing or invalid")
            logging.info("Reset config file..")
            input("Press Enter to continue...")
            welcome_tutorial()
    elif preset_choice == "2":
        clear()
        logging.info("Select a premade preset:")
        for i, mode in enumerate(PRESETS, start=1):
            logging.info(f"{i}. {mode}")
        preset_number = input("Option: ").strip()
        try:
            preset_number = int(preset_number)
            if 1 <= preset_number <= len(PRESETS):
                selected_preset = list(PRESETS.keys())[preset_number - 1]
                clear()
                last_mode = cfg.get('Settings', 'DynamicMode', fallback='0')
                cfg.set('Settings', 'DynamicMode', '0')
                user_mode = selected_preset
                apply_smu(PRESETS[user_mode], user_mode)
                cfg.set('Settings', 'DynamicMode', last_mode)
            else:
                logging.info("Invalid option.")
                input("Press Enter to continue...")
        except ValueError:
            logging.info("Invalid input. Please enter a number.")
    elif preset_choice.lower() == "d":
         last_mode = cfg.get('Settings', 'DynamicMode', fallback='0')
         last_apply = cfg.get('Settings', 'ReApply', fallback='0')
         cfg.set('Settings', 'DynamicMode', '1')
         cfg.set('Settings', 'ReApply', '1')
         apply_smu(PRESETS['Balance'], 'Balance')
         cfg.set('Settings', 'DynamicMode', last_mode)
         cfg.set('Settings', 'ReApply', last_apply)
    elif preset_choice.lower() == "b":
        return
    else:
        logging.info("Invalid option.")
        
def apply_smu(args, user_mode):
    sleep_time = cfg.get('Settings', 'Time', fallback='30')
    password = cfg.get('User', 'Password', fallback='')
    reapply = cfg.get('Settings', 'ReApply', fallback='0')
    dynamic = cfg.get('Settings', 'dynamicmode', fallback='0')
    prev_mode = None
    PRESETS = get_presets()
    if reapply == '1':
      while True:
        if dynamic == '1':
            battery_status = subprocess.check_output(["upower", "-i", "/org/freedesktop/UPower/devices/battery_BAT0"]).decode("utf-8")
            if 'state:               charging' in battery_status:
                user_mode = 'Extreme'
            elif 'state:               discharging' in battery_status:
                    user_mode = 'Eco'
            else:
                user_mode = 'Extreme'
        if prev_mode == user_mode and dynamic == '1':
            for _ in range(int(float(sleep_time))):
                for _ in range(1):
                    time.sleep(1)
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = sys.stdin.readline()
                        if line.lower().strip() == 'b':
                            return
            continue
        prev_mode = user_mode
        clear()
        if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", f"{current_dir}/Assets/ryzenadj"] + custom_args.split()
        else:
            args = PRESETS[user_mode]
            command = ["sudo", "-S", f"{current_dir}/Assets/ryzenadj"] + args.split()
        logging.info(f"Using preset: {user_mode}")
        dm_enabled = cfg.get('Settings', 'DynamicMode', fallback='0') == '1'
        if dm_enabled:
            logging.info("Dynamic mode: Enabled")
        else:
            logging.info("Dynamic mode: Disabled")
        logging.info(f"Script will check and auto reapply if need every {sleep_time} seconds")
        logging.info("Press B then Enter to go back to the main menu")
        logging.info("--------------- RyzenAdj Log ---------------")
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if cfg.get('Settings', 'Debug', fallback='1') == '1':
             if result.stderr:
                logging.info(f"{result.stderr.decode()}")
        for _ in range(int(float(sleep_time))):
            for _ in range(1):
                time.sleep(1)
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    line = sys.stdin.readline()
                    if line.lower().strip() == 'b':
                        return
    else:
          clear()
          if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", f"{current_dir}/Assets/ryzenadj"] + custom_args.split()
          else:
            args = PRESETS[user_mode]
            command = ["sudo", "-S", f"{current_dir}/Assets/ryzenadj"] + args.split()
          logging.info(f"Using preset: {user_mode}")
          logging.info("--------------- RyzenAdj Log ---------------")
          result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
          logging.info(result.stdout.decode())
          if cfg.get('Settings', 'Debug', fallback='1') == '1':
             if result.stderr:
                logging.info(f"{result.stderr.decode()}")
          input("Press Enter to continue...")

def main():
    check_cfg_integrity()
    PRESETS = get_presets()
    if cfg.get('Settings', 'SoftwareUpdate', fallback='0') == '1':
        check_updates()
    if cfg.get('Settings', 'ApplyOnStart', fallback='1') == '1':  
       if user_mode := read_cfg():
          if user_mode in PRESETS:
             apply_smu(PRESETS[user_mode], user_mode)
          else:
             apply_smu(user_mode, user_mode)
    while True:
        clear()
        options = {
            "1": preset_menu,
            "2": settings,
            "a": about,
            "q": lambda: sys.exit("\nThanks for using UXTU4Unix\nHave a nice day!"),
        }
        logging.info("1. Apply power management settings\n2. Settings")
        logging.info("")
        logging.info("A. About UXTU4Unix")
        logging.info("Q. Quit")
        choice = input("Option: ").lower().strip()
        if action := options.get(choice):
            action()
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
                
if __name__ == "__main__":
    main()