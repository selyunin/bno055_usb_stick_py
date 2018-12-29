#!/usr/bin/env python
import os
import os.path
import subprocess

from shutil import copy


def prompt_sudo():
    ret = 0
    if os.geteuid() != 0:
        msg = "[sudo] password for %u: "
        ret = subprocess.check_call("sudo -v -p '%s'" % msg, shell=True)
    return ret


def copy_rules_to_udev():
    rules_file = '97-ttyacm.rules'
    file_path = os.path.dirname(os.path.abspath(__file__))
    rules_file_abspath = os.path.join(file_path, rules_file)
    print(f"copying rules file: {rules_file_abspath} to /etc/udev/rules.d")
    subprocess.call(['sudo', 'cp', rules_file_abspath, '/etc/udev/rules.d'])


def reload_udev_rules():
    subprocess.call(['sudo', 'udevadm', 'control', '--reload-rules'])


def disable_modem_manager_bno():
    if prompt_sudo() != 0:
        print("ERROR: User should have root privileges! script will *NOT* be executed, exit")
        exit(1)
    copy_rules_to_udev()
    reload_udev_rules()


if __name__ == '__main__':
    disable_modem_manager_bno()
