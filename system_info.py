# encoding:utf-8
# _*_ coding: utf-8 _*_
import psutil
import os
import wmi

def bytes2human(n):
    # http://code.activestate.com/recipes/578019
    # >>> bytes2human(10000)
    # '9.8K'
    # >>> bytes2human(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

#CPU
def get_cpu_info():
    print ('\n------------------------------------------------------------------------')
    print('CPU\n------------------------------------------------------------------------')
    print ("cpu_percent:%7s" %str(psutil.cpu_percent(0.5)) + "%"),
    cpu_percent = psutil.cpu_percent(0.5)
    return cpu_percent

#Memory
def pprint_ntuple(nt):
    for name in nt._fields:
        value = getattr(nt, name)
        print
        if name != 'percent':
            value = bytes2human(value)
        print('%-10s : %7s' % (name.capitalize(), value)),

def get_memory_info():
    print ('\n------------------------------------------------------------------------')
    print('MEMORY\n------------------------------------------------------------------------'),
    pprint_ntuple(psutil.virtual_memory()),
    print ('\n------------------------------------------------------------------------'),
    print('\nSWAP\n------------------------------------------------------------------------'),
    pprint_ntuple(psutil.swap_memory()),
    return psutil.virtual_memory().percent

#Disk
def get_disk_info():
    print ('\n------------------------------------------------------------------------')
    print('Disk\n------------------------------------------------------------------------')
    templ = "%-17s %8s %8s %8s %5s%% %9s  %s"
    print(templ % ("Device", "Total", "Used", "Free", "Use ", "Type",
                   "Mount"))
    count = len(psutil.disk_partitions(all=False))
    i = 0
    j = 0
    disk_part = []
    disk_info = []
    # for i in range(count):
    #     disk_info.append(i)
    for part in psutil.disk_partitions(all=False):
        if os.name == 'nt':
            if 'cdrom' in part.opts or part.fstype == '':
                # skip cd-rom drives with no disk in it; they may raise
                # ENOENT, pop-up a Windows GUI error for a non-ready
                # partition or just hang.
                continue
        usage = psutil.disk_usage(part.mountpoint)
        print(templ % (
            part.device,
            bytes2human(usage.total),
            bytes2human(usage.used),
            bytes2human(usage.free),
            int(usage.percent),
            part.fstype,
            part.mountpoint))
        for i in range(1):
            disk_part.append(part.device.split(':')[0])
            disk_part.append(usage.percent)
        disk_info.append(disk_part)
        disk_part = []
    return disk_info
#Network
def poll():
    """Retrieve raw stats within an interval window."""
    tot_before = psutil.net_io_counters()
    pnic_before = psutil.net_io_counters(pernic=True)
    tot_after = psutil.net_io_counters()
    pnic_after = psutil.net_io_counters(pernic=True)
    return (tot_before, tot_after, pnic_before, pnic_after)

def get_net_info(tot_before, tot_after, pnic_before, pnic_after):
    """Print stats on screen."""
    print ('\n------------------------------------------------------------------------')
    print('Network\n------------------------------------------------------------------------')
    # totals
    print("total bytes:           sent: %-10s   received: %s" % (
        bytes2human(tot_after.bytes_sent),
        bytes2human(tot_after.bytes_recv))
    )
    print("total packets:         sent: %-10s   received: %s" % (
        tot_after.packets_sent, tot_after.packets_recv))

    # per-network interface details: let's sort network interfaces so
    # that the ones which generated more traffic are shown first
    print("")
    nic_names = list(pnic_after.keys())
    nic_names.sort(key=lambda x: sum(pnic_after[x]), reverse=True)
    for name in nic_names:
        stats_before = pnic_before[name]
        stats_after = pnic_after[name]
        templ = "%-15s %15s %15s"
        print(templ % (name, "TOTAL", "PER-SEC"))
        print(templ % (
            "bytes-sent",
            bytes2human(stats_after.bytes_sent),
            bytes2human(
                stats_after.bytes_sent - stats_before.bytes_sent) + '/s',
        ))
        print(templ % (
            "bytes-recv",
            bytes2human(stats_after.bytes_recv),
            bytes2human(
                stats_after.bytes_recv - stats_before.bytes_recv) + '/s',
        ))
        print(templ % (
            "pkts-sent",
            stats_after.packets_sent,
            stats_after.packets_sent - stats_before.packets_sent,
        ))
        print(templ % (
            "pkts-recv",
            stats_after.packets_recv,
            stats_after.packets_recv - stats_before.packets_recv,
        ))
        print("")

def get_sys_version():
    c = wmi.WMI()
    # 获取操作系统版本
    for sys in c.Win32_OperatingSystem():
        return sys


def get_ip():
    c = wmi.WMI()
    # 获取MAC和IP地址
    for interface in c.Win32_NetworkAdapterConfiguration(IPEnabled=1):
        return interface.IPAddress


def get_mac():
    for interface in wmi.WMI().Win32_NetworkAdapterConfiguration(IPEnabled=1):
        return interface.MACAddress





