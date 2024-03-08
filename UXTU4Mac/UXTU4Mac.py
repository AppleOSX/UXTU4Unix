import os, time, subprocess, getpass, webbrowser, logging, sys, binascii
import urllib.request, plistlib, base64, json, hashlib, select
from configparser import ConfigParser

CONFIG_PATH = 'config.ini'
LATEST_VERSION_URL = "https://github.com/AppleOSX/UXTU4Mac/releases/latest"
GITHUB_API_URL = "https://api.github.com/repos/AppleOSX/UXTU4Mac/releases/latest"
LOCAL_VERSION = "0.1.9"

PRESETS = {
    "Eco": "--tctl-temp=95 --apu-skin-temp=45 --stapm-limit=6000 --fast-limit=8000 --stapm-time=64 --slow-limit=6000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000",
    "Performance": "--tctl-temp=95 --apu-skin-temp=95 --stapm-limit=28000 --fast-limit=28000 --stapm-time=64 --slow-limit=28000 --slow-time=128 --vrm-current=180000 --vrmmax-current=180000 --vrmsoc-current=180000 --vrmsocmax-current=180000 --vrmgfx-current=180000 ",
    "Extreme": "--max-performance",
    "Balance": "--power-saving"
}

os.makedirs('Logs', exist_ok=True)
logging.basicConfig(filename='Logs/UXTU4Mac.log', filemode='w', encoding='utf-8',
                    level=logging.INFO, format='%(levelname)s %(asctime)s %(message)s',
                    datefmt='%d/%m/%Y %H:%M:%S')
logging.getLogger().addHandler(logging.StreamHandler())
cfg = ConfigParser()
cfg.read(CONFIG_PATH)
current_dir = os.path.dirname(os.path.realpath(__file__))
command_file = os.path.join(current_dir, 'UXTU4Mac.command')
command_file_name = os.path.basename(command_file)

def clear():
    os.system('clear')
    logging.info(r"""   _   ___  _______ _   _ _ _  __  __
  | | | \ \/ /_   _| | | | | ||  \/  |__ _ __
  | |_| |>  <  | | | |_| |_  _| |\/| / _` / _|
   \___//_/\_\ |_|  \___/  |_||_|  |_\__,_\__|
  Version: {}
""".format(LOCAL_VERSION))
    
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

def hardware_info():
    clear()
    logging.info("Device Information:")
    logging.info(f' - Name: {get_hardware_info("scutil --get ComputerName")}')
    logging.info(f' - Model (SMBios): {get_hardware_info("sysctl -n hw.model")}')
    logging.info(
        f""" - {get_hardware_info("system_profiler SPHardwareDataType | grep 'Serial Number'")}"""
    )
    logging.info(f' - macOS version: {get_hardware_info("sysctl -n kern.osproductversion")} ({get_hardware_info("sysctl -n kern.osversion")})')

    logging.info("\nProcessor Information:")
    logging.info(
        f' - Processor: {get_hardware_info("sysctl -n machdep.cpu.brand_string")}'
    )
    cpu_family = get_hardware_info("Assets/ryzenadj -i | grep 'CPU Family'", use_sudo=True).strip()
    smu_version = get_hardware_info("Assets/ryzenadj -i | grep 'SMU BIOS Interface Version'", use_sudo=True).strip()
    if cpu_family:
        logging.info(f' - {cpu_family}')
    if smu_version:
        logging.info(f' - {smu_version}')
    logging.info(f' - Cores: {get_hardware_info("sysctl -n hw.physicalcpu")}')
    logging.info(f' - Threads: {get_hardware_info("sysctl -n hw.logicalcpu")}')
    logging.info(
        f""" - {get_hardware_info("system_profiler SPHardwareDataType | grep 'L2'")}"""
    )
    logging.info(
        f""" - {get_hardware_info("system_profiler SPHardwareDataType | grep 'L3'")}"""
    )
    base_clock = float(get_hardware_info("sysctl -n hw.cpufrequency_max")) / (10**9)
    logging.info(" - Base clock: {:.2f} GHz".format(base_clock))
    logging.info(f' - Vendor: {get_hardware_info("sysctl -n machdep.cpu.vendor")}')
    logging.info(
        f' - Instruction: {get_hardware_info("sysctl -a | grep machdep.cpu.features").split(": ")[1]}'
    )
    logging.info("\nMemory Information:")
    memory = float(get_hardware_info("sysctl -n hw.memsize")) / (1024**3)
    logging.info(" - Total of RAM: {:.2f} GB".format(memory))
    ram_info = get_hardware_info("system_profiler SPMemoryDataType")
    ram_info_lines = ram_info.split('\n')
    ram_slot_names = ["BANK","SODIMM","DIMM"]
    slot_info = []
    try:
        for i, line in enumerate(ram_info_lines):  
           if any(slot_name in line for slot_name in ram_slot_names): 
             slot_name = line.strip()
             size = ram_info_lines[i+2].strip().split(":")[1].strip()
             type = ram_info_lines[i+3].strip().split(":")[1].strip()
             speed = ram_info_lines[i+4].strip().split(":")[1].strip()
             manufacturer = ram_info_lines[i+5].strip().split(":")[1].strip()
             part_number = ram_info_lines[i+6].strip().split(":")[1].strip()
             serial_number = ram_info_lines[i+7].strip().split(":")[1].strip()
             slot_info.append((slot_name, size, type, speed, manufacturer, part_number, serial_number))
        for i in range(0, len(slot_info), 2):
            logging.info(
                f" - Size: {slot_info[i][1]} / {slot_info[i + 1][1] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Type: {slot_info[i][2]} / {slot_info[i + 1][2] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Speed: {slot_info[i][3]} / {slot_info[i + 1][3] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Manufacturer: {slot_info[i][5]} / {slot_info[i + 1][5] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Status: {slot_info[i][4]} / {slot_info[i + 1][4] if i + 1 < len(slot_info) else 'N/A'}"
            )
            logging.info(
                f" - Part Number: {slot_info[i][6]} / {slot_info[i + 1][6] if i + 1 < len(slot_info) else 'N/A'}"
            )
    except:
        logging.info("Pardon me for my horrible search for displaying RAM information")
    if has_battery := get_hardware_info(
        "system_profiler SPPowerDataType | grep 'Battery Information'"
    ):
        logging.info("\nBattery Information:")
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Manufacturer'")}"""
        )
        logging.info(" - State of Charge (%): {}".format(get_hardware_info("pmset -g batt | egrep '([0-9]+\\%).*' -o --colour=auto | cut -f1 -d';'")))
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Cycle Count'")}"""
        )
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Full Charge Capacity'")}"""
        )
        logging.info(
            f""" - {get_hardware_info("system_profiler SPPowerDataType | grep 'Condition'")}"""
        )
    logging.info("")
    SIP = cfg.get('User', 'SIP', fallback='03080000')
    logging.info("UXTU4Mac dependencies:")
    result = subprocess.run(['nvram', 'boot-args'], capture_output=True, text=True)
    if 'debug=0x144' not in result.stdout:
        logging.info(" - debug=0x144: Missing")
    else:
        logging.info(" - debug=0x144: OK")
    result = subprocess.run(['nvram', 'csr-active-config'], capture_output=True, text=True)
    if SIP not in result.stdout.replace('%', ''):
        logging.info(" - SIP: Not set / Incorrect flags")
    else:
        logging.info(" - SIP: OK")
    logging.info("")
    input("Press Enter to continue...")

def about():
    options = {
        "1": lambda: webbrowser.open("https://www.github.com/AppleOSX/UXTU4Mac"),
        "t": tester_list,
        "f": updater,
        "b": "break"
    }
    while True:
        clear()
        logging.info("About UXTU4Mac")
        logging.info("The Loop Update (1FR2ED0M)")
        logging.info("----------------------------")
        logging.info("Maintainer: GorouFlex\nCLI: GorouFlex")
        logging.info("GUI: NotchApple1703\nAdvisor: NotchApple1703")
        logging.info("Command file: CorpNewt")
        logging.info("----------------------------")
        logging.info("T. Tester list")
        logging.info(f"F. Force update to the latest version ({get_latest_ver()})")
        logging.info("\nB. Back")
        choice = input("Option: ").lower()
        action = options.get(choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def tester_list():
    clear()
    logging.info("Special thanks to our testers:")
    logging.info("")
    logging.info("- GorouFlex for testing on Internal Beta Test Program")
    logging.info("- GorouFlex for testing on AMD Ryzen 5 4500U (Renoir)")
    logging.info("- nlqanh524 for testing on AMD Ryzen 5 5500U (Lucienne)")
    logging.info("")
    input("Press Enter to continue...")
    
def settings():
    options = {
        "1": preset_cfg,
        "2": sleep_cfg,
        "3": dynamic_cfg,
        "4": login_cfg,
        "5": cfu_cfg,
        "6": fip_cfg,
        "7": pass_cfg,
        "8": sip_cfg,
        "i": install_menu,
        "r": reset,
        "b": "break"
    }
    while True:
        clear()
        logging.info("--------------- Settings ---------------")
        logging.info("1. Preset\n2. Sleep time")
        logging.info("3. Dynamic Mode (Beta)")
        logging.info("4. Run on Startup\n5. Software Update")
        logging.info("6. File Integrity Protection\n7. Sudo password")
        logging.info("8. SIP Flags\n")
        logging.info("I. Install UXTU4Mac dependencies")
        logging.info("R. Reset all saved settings")
        logging.info("B. Back")
        settings_choice = input("Option: ").lower()
        action = options.get(settings_choice, None)
        if action is None:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
        elif action == "break":
            break
        else:
            action()

def reset():
    os.remove(CONFIG_PATH)
    clear()
    logging.info("Reset successfully")
    input("Press Enter to continue...")
    welcome_tutorial()

def sip_cfg():
    while True:
        clear()
        logging.info("--------------- SIP Flags---------------")
        logging.info("(Change your required SIP Flags)")
        SIP = cfg.get('User', 'SIP', fallback='03080000')
        logging.info(f"Current required SIP: {SIP}")
        logging.info("")
        logging.info("1. Change SIP Flags\n")
        logging.info("B. Back")
        choice = input("Option: ")
        if choice == "1":
            logging.info("Caution: Must have atleast ALLOW_UNTRUSTED_KEXTS (0x1)")
            SIP = input("Enter your required SIP Flags: ")
            cfg.set('User', 'SIP', SIP)
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            continue
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def dynamic_cfg():
    while True:
        clear()
        logging.info("--------------- Dynamic Mode (Beta) ---------------")
        logging.info("(Automatically switch preset based on your CPU and RAM usage)")
        dm_enabled = cfg.get('User', 'DynamicMode', fallback='0') == '1'
        if dm_enabled:
            logging.info("Status: Enabled")
        else:
            logging.info("Status: Disabled")
        logging.info("")
        logging.info("1. Enable Dynamic Mode\n2. Disable Dynamic Mode\n")
        logging.info("B. Back")
        choice = input("Option: ")
        if choice == "1":
            cfg.set('User', 'DynamicMode', '1')
        elif choice == "2":
            cfg.set('User', 'DynamicMode', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            continue
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
            
def preset_menu():
    clear()
    logging.info("Apply power management settings:")
    logging.info("1. Load saved settings from config file\n2. Load from available premade preset\n\nD. Dynamic Mode (Beta)\nC. Custom (Beta)")
    logging.info("B. Back")
    preset_choice = input("Option: ")
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
        preset_number = input("Option: ")
        try:
            preset_number = int(preset_number)
            if 1 <= preset_number <= len(PRESETS):
                selected_preset = list(PRESETS.keys())[preset_number - 1]
                clear()
                user_mode = selected_preset
                apply_smu(PRESETS[user_mode], user_mode)
            else:
                logging.info("Invalid option.")
                input("Press Enter to continue...")
        except ValueError:
            logging.info("Invalid input. Please enter a number.")
    elif preset_choice.lower() == "d":
         cfg.set('User', 'DynamicMode', '1')
         apply_smu(PRESETS['Balance'], 'Balance')
    elif preset_choice.lower() == "c":
        custom_args = input("Custom arguments: ")
        clear()
        user_mode = "Custom"
        apply_smu(custom_args, user_mode)
    elif preset_choice.lower() == "b":
        return
    else:
        logging.info("Invalid option.")
        
def sleep_cfg():
    while True:
        clear()
        logging.info("--------------- Sleep time ---------------")
        logging.info("(Sleep time between next apply to SMU using ryzenAdj)")
        time = cfg.get('User', 'Time', fallback='30')
        logging.info(f"Current sleep time: {time}")
        logging.info("\n1. Change sleep time\n\nB. Back")
        choice = input("Option: ")
        if choice == "1":
            set_time = input("Enter your sleep time (Default is 30s): ")
            cfg.set('User', 'Time', set_time)
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
        logging.info("--------------- Sudo password ---------------")
        pswd = cfg.get('User', 'Password', fallback='')
        logging.info(f"Current sudo (login) password: {pswd}")
        logging.info("\n1. Change password\n\nB. Back")
        choice = input("Option: ")
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

def login_cfg():
    while True:
        clear()
        logging.info("--------------- Run on Startup ---------------")
        check_command = f"osascript -e 'tell application \"System Events\" to get the name of every login item' | grep {command_file_name}"
        login_enabled = subprocess.call(check_command, shell=True, stdout=subprocess.DEVNULL) == 0
        if login_enabled:
            logging.info("Status: Enable")
        else:
            logging.info("Status: Disable")
        logging.info("")
        logging.info("1. Enable Run on Startup\n2. Disable Run on Startup\n")
        logging.info("B. Back")
        choice = input("Option: ")
        if choice == "1":
            if not login_enabled:
               command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
               subprocess.call(command, shell=True)
            else:
                logging.info("You already add this script to Login Items")
                input("Press Enter to continue")
        elif choice == "2":
            if login_enabled:
              command = f"osascript -e 'tell application \"System Events\" to delete login item \"{command_file_name}\"'"
              subprocess.call(command, shell=True)
            else:
              logging.info("Cannot remove this script because it's does not exist on Login Items")
              input("Press Enter to continue")
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            continue

def cfu_cfg():
    while True:
        clear()
        logging.info("--------------- Software Update ---------------")
        cfu_enabled = cfg.get('User', 'SoftwareUpdate', fallback='1') == '1'
        if cfu_enabled:
            logging.info("Status: Enabled")
        else:
            logging.info("Status: Disabled")
        logging.info("")
        logging.info("1. Enable Software Update\n2. Disable Software Update\n")
        logging.info("B. Back")
        choice = input("Option: ")
        if choice == "1":
            cfg.set('User', 'SoftwareUpdate', '1')
        elif choice == "2":
            fip_enabled = cfg.get('User', 'FIP', fallback='0') == '1'
            if fip_enabled:
                logging.info("Cannot disable Software Update because File Integrity Protection is currently on")
                input("Press Enter to continue...")
                continue
            else:
                cfg.set('User', 'SoftwareUpdate', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            continue
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def fip_cfg():
    while True:
        clear()
        logging.info("--------------- File Integrity Protection ---------------")
        fip_enabled = cfg.get('User', 'FIP', fallback='0') == '1'
        if fip_enabled:
            logging.info("Status: Enabled")
        else:
            logging.info("Status: Disabled")
        logging.info("")
        logging.info("1. Enable File Integrity Protection\n2. Disable File Integrity Protection\n")
        logging.info("B. Back")
        choice = input("Option: ")
        cfu_enabled = cfg.get('User', 'SoftwareUpdate', fallback='1') == '1'
        if choice == "1":
            if cfu_enabled:
                cfg.set('User', 'FIP', '1')
            else:
                logging.info("Cannot enable File Integrity Protection because Software Update is currently Off")
                input("Press Enter to continue...")
                continue
        elif choice == "2":
            cfg.set('User', 'FIP', '0')
        elif choice.lower() == "b":
            break
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            continue
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)

def preset_cfg():
    clear()
    logging.info("--------------- Preset ---------------")
    logging.info("Preset:")
    for i, mode in enumerate(PRESETS, start=1):
        logging.info(f"{i}. {mode}")
    logging.info("\nD. Dynamic Mode (Beta)")
    logging.info("C. Custom (Beta)")
    logging.info("B. Back")
    logging.info("We recommend using the Dynamic Mode for normal tasks and better power management")
    choice = input("Option: ")
    if choice.lower() == 'c':
        custom_args = input("Enter your custom arguments: ")
        cfg.set('User', 'Mode', 'Custom')
        cfg.set('User', 'CustomArgs', custom_args)
        logging.info("Set preset sucessfully!")
        input("Press Enter to continue...")
    elif choice.lower() == 'd':
         cfg.set('User', 'DynamicMode', '1')
         cfg.set('User', 'Mode', 'Balance')
    elif choice.lower() == 'b':
        return
    else:
        try:
            preset_number = int(choice)
            preset_name = list(PRESETS.keys())[preset_number - 1]
            cfg.set('User', 'Mode', preset_name)
            logging.info("Set preset sucessfully!")
            input("Press Enter to continue...")
        except ValueError:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
            preset_cfg()
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    
def welcome_tutorial():
    if not cfg.has_section('User'):
        cfg.add_section('User')
    clear()
    logging.info("Welcome to UXTU4Mac!")
    logging.info("Created by GorouFlex, designed for AMD Zen-based processors on macOS.")
    logging.info("Based on RyzenAdj and inspired by UXTU.")
    logging.info("Let's get started with some initial setup.")
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
    check_command = f"osascript -e 'tell application \"System Events\" to get the name of every login item' | grep {command_file_name}"
    login_enabled = subprocess.call(check_command, shell=True, stdout=subprocess.DEVNULL) == 0
    if not login_enabled:
        start_with_macos = input("Do you want this script to start with macOS? (Login Items) (y/n): ").lower()
        if start_with_macos == 'y':
            command = f"osascript -e 'tell application \"System Events\" to make login item at end with properties {{path:\"{command_file}\", hidden:false}}'"
            subprocess.call(command, shell=True)
        with open(CONFIG_PATH, 'w') as config_file:
            cfg.write(config_file)
    try:
        cfg.set('User', 'Password', password)
        cfg.set('User', 'Time', '30')
        cfg.set('User', 'DynamicMode', '0')
        cfg.set('User', 'SIP', '03080000')
        cfg.set('User', 'SoftwareUpdate', '1')
        cfg.set('User', 'FIP', '0')
    except ValueError:
        logging.info("Invalid option.")
        raise SystemExit
    with open(CONFIG_PATH, 'w') as config_file:
        cfg.write(config_file)
    preset_cfg()
    clear()
    if not check_run():
       install_menu()

def edit_config(config_path):
    SIP = cfg.get('User', 'SIP', fallback='03080000')
    with open(config_path, 'rb') as f:
        config = plistlib.load(f)
    if 'NVRAM' in config and 'Add' in config['NVRAM'] and '7C436110-AB2A-4BBB-A880-FE41995C9F82' in config['NVRAM']['Add']:
        if 'boot-args' in config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']:
            boot_args = config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['boot-args']
            if 'debug=0x144' not in boot_args:
                config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82'][
                    'boot-args'
                ] = f'{boot_args} debug=0x144'
        SIP_bytes = binascii.unhexlify(SIP)
        config['NVRAM']['Add']['7C436110-AB2A-4BBB-A880-FE41995C9F82']['csr-active-config'] = SIP_bytes
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

def read_cfg() -> str:
    return cfg.get('User', 'Mode', fallback='')

def check_cfg_integrity() -> None:
    if not os.path.isfile(CONFIG_PATH) or os.stat(CONFIG_PATH).st_size == 0:
        welcome_tutorial()
        return
    cfg = ConfigParser()
    cfg.read(CONFIG_PATH)
    required_keys = ['password', 'softwareupdate', 'fip', 'dynamicmode', 'time', 'mode']
    if not cfg.has_section('User') or any(key not in cfg['User'] for key in required_keys):
        welcome_tutorial()

def get_latest_ver():
    latest_version = urllib.request.urlopen(LATEST_VERSION_URL).geturl()
    return latest_version.split("/")[-1]

def get_changelog():
    request = urllib.request.Request(GITHUB_API_URL)
    response = urllib.request.urlopen(request)
    data = json.loads(response.read())
    return data['body']

def check_run():
    SIP = cfg.get('User', 'SIP', fallback='03080000')
    result = subprocess.run(['nvram', 'boot-args'], capture_output=True, text=True)
    if 'debug=0x144' not in result.stdout:
        return False
    result = subprocess.run(['nvram', 'csr-active-config'], capture_output=True, text=True)
    return SIP in result.stdout.replace('%', '')

def install_menu():
    clear()
    logging.info("UXTU4Mac dependencies\n")
    logging.info("1. Auto install (Default path: /Volumes/EFI/EFI/OC)\n2. Manual install (Specify your config.plist path)\n")
    logging.info("B. Back")
    choice = input("Option (default is 1): ")
    if choice == "1":
        install_auto()
    elif choice == "2":
        install_manual()
    elif choice.lower() == "b":
        return
    else:
        logging.info("Invalid option. Please try again.")
        input("Press Enter to continue...")
        
def install_auto():
    clear()
    logging.info("Installing UXTU4Mac dependencies (Auto)...")
    password = cfg.get('User', 'Password', fallback='')
    try:
        subprocess.run(["sudo", "-S", "diskutil", "mount", "EFI"], input=password.encode(), check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to mount EFI partition: {e}")
        logging.error("Please run in Manual mode.")
        input("Press Enter to continue...")
        return
    oc_path = os.path.join("/Volumes/EFI/EFI/OC")
    if not os.path.exists(oc_path):
        logging.error("OC folder does not exist!")
        input("Press Enter to continue...")
        subprocess.run(["sudo", "diskutil", "unmount", "force", "EFI"], input=password.encode(), check=True)
        return
    config_path = os.path.join("/Volumes/EFI/EFI/OC/config.plist")
    edit_config(config_path)
    logging.info("Successfully updated boot-args and SIP settings.")
    subprocess.run(["sudo", "diskutil", "unmount", "force", "EFI"], input=password.encode(), check=True)
    logging.info("UXTU4Mac dependencies installation completed.")
    choice = input("Do you want to restart your computer to take effects? (y/n)")
    if choice.lower() == "y":
        input("Saved your current work before restarting. Press Enter to continue")
        restart_command = '''osascript -e 'tell app "System Events" to restart' '''
        subprocess.call(restart_command, shell=True)

def install_manual():
    clear()
    logging.info("Installing UXTU4Mac dependencies (Manual)...")
    password = cfg.get('User', 'Password', fallback='')
    config_path = input("Please drag and drop the target plist: ").strip()
    if not os.path.exists(config_path):
        logging.error(f"The specified path '{config_path}' does not exist.")
        input("Press Enter to continue...")
        return
    edit_config(config_path)
    logging.info("Successfully updated boot-args and SIP settings.")
    logging.info("UXTU4Mac dependencies installation completed.")
    choice = input("Do you want to restart your computer to take effects? (y/n)")
    if choice.lower() == "y":
        input("Saved your current work before restarting. Press Enter to continue")
        restart_command = '''osascript -e 'tell app "System Events" to restart' '''
        subprocess.call(restart_command, shell=True)
        
def updater():
    clear()
    changelog = get_changelog()
    logging.info("--------------- UXTU4Mac Software Update ---------------")
    logging.info("A new update is available!")
    logging.info(
        f"Changelog for the latest version ({get_latest_ver()}):\n{changelog}"
    )
    logging.info("Do you want to update? (y/n): ")
    choice = input("Option: ").lower()
    if choice == "y":    
        subprocess.run(["python3", "Assets/SU.py"])
        logging.info("Updating...")
        logging.info("Update complete. Restarting the application, please close this window...")
        command_file_path = os.path.join(os.path.dirname(__file__), 'UXTU4Mac.command')
        subprocess.Popen(['open', command_file_path])
    elif choice == "n":
        logging.info("Skipping update...")
    else:
        logging.info("Invalid option.")
    raise SystemExit

def check_updates():
    try:
        latest_version = get_latest_ver()
    except:
        clear()
        logging.info("No Internet connection. Please try again.")
        raise SystemExit
    if LOCAL_VERSION < latest_version:
        updater()
    elif LOCAL_VERSION > latest_version:
        clear()
        logging.info("Welcome to the UXTU4Mac Beta Program.")
        logging.info("This build may not be as stable as expected")
        logging.info("It's intended only for testing purposes!")
        result = input("Do you want to continue? (y/n): ").lower()
        if result != "y":
            logging.info("Quitting...")
            raise SystemExit

def apply_smu(args, user_mode):
    if not check_run():
        clear()
        logging.info("Cannot run RyzenAdj because your computer is missing debug=0x144 or required SIP is not SET yet\nPlease run Install UXTU4Mac dependencies under Setting \nand restart after install.")
        input("Press Enter to continue...")
        return
    sleep_time = cfg.get('User', 'Time', fallback='30')
    password = cfg.get('User', 'Password', fallback='')
    dynamic = cfg.get('User', 'DynamicMode', fallback='0')
    while True:
        if dynamic == '1':
            cpu_usage = os.popen("ps -A -o %cpu").readlines()
            cpu_usage = [float(i) for i in cpu_usage[1:] if i]
            ram_usage = os.popen("ps -A -o %mem").readlines()
            ram_usage = [float(i) for i in ram_usage[1:] if i]
            if any(i > 70 for i in cpu_usage) or any(i > 70 for i in ram_usage):
               user_mode = 'Extreme'
            elif all(10 <= i <= 70 for i in cpu_usage) or all(10 <= i <= 70 for i in ram_usage):
               user_mode = 'Balance'
            elif all(i < 10 for i in cpu_usage) or all(i < 10 for i in ram_usage):
               user_mode = 'Eco'
        if args == 'Custom':
            custom_args = cfg.get('User', 'CustomArgs', fallback='')
            command = ["sudo", "-S", "Assets/ryzenadj"] + custom_args.split()
        else:
            args = PRESETS[user_mode]
        command = ["sudo", "-S", "Assets/ryzenadj"] + args.split()
        clear()
        logging.info(f"Using preset: {user_mode}")
        dm_enabled = cfg.get('User', 'DynamicMode', fallback='0') == '1'
        if dm_enabled:
            logging.info("Dynamic mode: Enabled")
        else:
            logging.info("Dynamic mode: Disabled")
        logging.info(f"Script will be reapplied every {sleep_time} seconds")
        logging.info("Press B then Enter to go back to the main menu")
        logging.info("(Please ignore the 'Password:')")
        logging.info("--------------- RyzenAdj Log ---------------")
        result = subprocess.run(command, input=password.encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(result.stdout.decode())
        if result.stderr:
            logging.info(f"{result.stderr.decode()}")
        for _ in range(int(float(sleep_time))):
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                line = sys.stdin.readline()
                if line.lower().strip() == 'b':
                    return
            time.sleep(1)

def check_file_integrity():
    hash_file_url = 'https://raw.githubusercontent.com/AppleOSX/UXTU4Mac/master/Hash.txt'
    try:
        with urllib.request.urlopen(hash_file_url) as response:
            expected_hash = response.read().decode().strip()
    except urllib.error.URLError:
        clear()
        logging.error(f"File Integrity Protection: {hash_file_url} not found. Resetting...")
        reset()
    with open(__file__, 'rb') as file:
        file_content = file.read()
    current_hash = hashlib.sha256(file_content).hexdigest()
    if current_hash != expected_hash:
        clear()
        logging.error("File Integrity Protection: File has been modified!\nOr this version is outdated.\nExiting...")
        raise SystemExit
    
def main():
    check_cfg_integrity()
    if cfg.get('User', 'SoftwareUpdate', fallback='1') == '1':
        check_updates()
    if cfg.get('User', 'FIP', fallback='0') == '1':
        check_file_integrity()
    time = cfg.get('User', 'Time', fallback='30')
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
            "h": hardware_info,
            "a": about,
            "q": lambda: sys.exit("\nThanks for using UXTU4Mac\nHave a nice day!"),
        }
        logging.info("1. Apply power management settings\n2. Settings")
        logging.info("")
        logging.info("H. Hardware Information")
        logging.info("A. About UXTU4Mac")
        logging.info("Q. Quit")
        choice = input("Option: ").lower()
        if action := options.get(choice):
            action()
        else:
            logging.info("Invalid option.")
            input("Press Enter to continue...")
                
if __name__ == "__main__":
    main()
