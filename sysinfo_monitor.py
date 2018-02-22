# -*- coding: utf-8 -*-
#encoding:utf-8
import conn_mssql
import conn_oracle
import system_info
import time
import os
import re
import sys
import socket
import ConfigParser
import traceback
import logging

reload(sys)
sys.setdefaultencoding('utf8')

#获取配置文件信息内容
def get_config():
    if get_replace():
        conf = ConfigParser.ConfigParser()
        conf.read("sysMon_config.conf")
        return conf

#\xfe\xff(xff\xfe)或\xef\xbb\xbf
def get_replace():
    # windows下用记事本打开配置文件并修改保存后,编码为unicode或utf-8的文件的文件头
    # 会被相应的加上\xfe\xff(xff\xfe)或\xef\xbb\xbf,ConfigParser解析时会出错，因此解析之前，先替换掉
    try:
        content = open('sysMon_config.conf').read()
        if re.search(r"\xfe\xff",content) or re.search(r"\xff\xfe", content) or re.search(r"\xef\xbb\xbf", content):
            content = re.sub(r"\xfe\xff", "", content)
            content = re.sub(r"\xff\xfe", "", content)
            content = re.sub(r"\xef\xbb\xbf", "", content)
            open('sysMon_config.conf', 'w').write(content)
            print u"\\xfe\\xff已去掉",
            print u"\\xff\\xfe已去掉",
            print u"\\xef\\xbb\\xbf已去掉"
        return True
    except:
        print u"配置文件解析出错"
        traceback.print_exc()
        return False
    finally:
        pass

def get_ipaddr():
    try:
        hostname = socket.gethostname()
        ipaddress = socket.gethostbyname(hostname)
        return ipaddress
    except:
        print u"获取本地IP失败"
        traceback.print_exc()
        return False
    finally:
        pass

def get_mssql_conn():
    host = get_config().get("mssql_info", "host")
    port = get_config().get("mssql_info", "port")
    user = get_config().get("mssql_info", "user")
    pwd = get_config().get("mssql_info", "pwd")
    db = get_config().get("mssql_info", "db")
    ms = conn_mssql.MSSQL(host, port, user, pwd, db)
    return ms

def get_oracle_conn():
    host = get_config().get("oracle_info", "host")
    port = get_config().get("oracle_info", "port")
    user = get_config().get("oracle_info", "user")
    pwd = get_config().get("oracle_info", "pwd")
    db = get_config().get("oracle_info", "db")
    ora = conn_oracle.Oracle(host, port, user, pwd, db)
    return ora

def compare_time(start_time,end_time):
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    cur_time = time.mktime(time.strptime(t,'%Y-%m-%d %H:%M:%S'))
    s_time = time.mktime(time.strptime(start_time,'%Y-%m-%d %H:%M:%S'))
    e_time = time.mktime(time.strptime(end_time,'%Y-%m-%d %H:%M:%S'))
    # print "curtime = %s,s_time = %s,e_time = %s" %(cur_time,s_time,e_time)
    if (float(e_time)) >= (float(s_time)):
        if ((float(cur_time)) >= (float(s_time)) and (float(cur_time))<=(float(e_time))):
            return True
        else:
            return False
    else:
        if (float(s_time)) >= (float(e_time)):
            if ((float(cur_time)) >= (float(e_time)) and (float(cur_time))<=(float(s_time))):
                return False
            else:
                return True

def get_clear():
    if os.name == 'nt':
        os.system("cls")
    else:
        os.system("clear")

#监控信息插入到数据库
def get_insert_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip):
    insert_str = "insert into " + tableName + " (xtid,cpu_percent,disk_name,disk_usage,mem_percent,cur_time,ip) VALUES ('" + xtid + "','" + str(cpu_percent) + "','" + disk_usage_max[0] + "','" + str(disk_usage_max[1]) + "','" + str(mem_percent) + "','" + cur_time + "','" + ip + "')"
    return insert_str

#监控信息更新到数据库
def get_update_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip):
    update_str = "update " + tableName + " set xtid = '" + xtid + "',cpu_percent = '" + str(cpu_percent) + "',disk_name = '" + disk_usage_max[0] + "',disk_usage = '" + str(disk_usage_max[1]) + "',mem_percent = '" + str(mem_percent)+ "',cur_time = '" + cur_time + "' where ip ='" + ip + "'"
    return update_str

def mssql_monitor(ip,xtid,cpu_percent,mem_percent,disk,cur_time,cpu_threshold,mem_threshold,disk_threshold,length):
    try:
        for i in range(length):
            if i == 0:
                disk_usage_max = disk[i]
            else:
                if disk_usage_max[1] < disk[i][1]:
                    disk_usage_max = disk[i]
        db = get_config().get("mssql_info", "db")
        tableName = get_config().get("mssql_info", "tableName")
        table_exists = get_mssql_conn().ExecQuery(
            "select COUNT(1) from " + db + "..sysobjects where xtype = 'U' and name = '" + tableName + "';")
        if table_exists:
            if table_exists[0][0] == 0:
                create_table = "CREATE TABLE " + db + "." + tableName + "(" \
                                                                        "[xtid] [int] NOT NULL," \
                                                                        "[cpu_percent] [float] NULL," \
                                                                        "[disk_name] [varchar](50) NULL," \
                                                                        "[disk_usage] [float] NULL," \
                                                                        "[mem_percent] [float] NULL," \
                                                                        "[cur_time] [nvarchar](50) NULL," \
                                                                        "[ip] [nchar](60) NOT NULL," \
                                                                        "[err_info] [text] NULL," \
                                                                        "[is_normal] [nchar](10) NULL," \
                                                                        "CONSTRAINT [PK_" + tableName + "] PRIMARY KEY CLUSTERED " \
                                                                                                        "(" \
                                                                                                        "[xtid] ASC," \
                                                                                                        "[ip] ASC" \
                                                                                                        ")WITH (PAD_INDEX  = OFF, STATISTICS_NORECOMPUTE  = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS  = ON, ALLOW_PAGE_LOCKS  = ON) ON [PRIMARY]" \
                                                                                                        ") ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]"
                get_mssql_conn().ExecCreate_table(create_table)
            else:
                resList = get_mssql_conn().ExecQuery(
                    "SELECT * FROM " + tableName + " where xtid = '" + xtid + "' and ip = '" + ip + "'")
                if not resList:
                    insert_str = get_insert_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip)
                    get_mssql_conn().ExecInsert(insert_str)
                    if float(cpu_percent) >= float(cpu_threshold) or float(mem_percent) >= float(
                            mem_threshold) or float(disk_usage_max[1]) >= float(disk_threshold):
                        if float(cpu_percent) > float(cpu_threshold):
                            if float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) < float(disk_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和内存利用率过高' + "' where ip = '" + ip + "'")
                            elif float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    mem_percent) < float(mem_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和磁盘利用率过高' + "' where ip = '" + ip + "'")
                            elif float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) >= float(disk_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU,内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU利用率过高' + "' where ip = '" + ip + "'")
                        elif (mem_percent) >= float(mem_threshold):
                            if float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    cpu_percent) < float(cpu_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存利用率过高' + "' where ip = '" + ip + "'")
                        else:
                            get_mssql_conn().ExecUpdate(
                                "update " + tableName + " set is_normal = '0',err_info = '" + u'磁盘利用率过高' + "' where ip = '" + ip + "'")
                    else:
                        get_mssql_conn().ExecUpdate(
                            "update " + tableName + " set is_normal = '1',err_info = '" + u'CPU,内存及磁盘利用率正常' + "' where ip = '" + ip + "'")
                else:
                    update_str = get_update_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip)
                    get_mssql_conn().ExecUpdate(update_str)
                    if float(cpu_percent) >= float(cpu_threshold) or float(mem_percent) >= float(
                            mem_threshold) or float(disk_usage_max[1]) >= float(disk_threshold):
                        if float(cpu_percent) > float(cpu_threshold):
                            if float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) < float(disk_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和内存利用率过高' + "' where ip = '" + ip + "'")
                            elif float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    mem_percent) < float(mem_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和磁盘利用率过高' + "' where ip = '" + ip + "'")
                            elif float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) >= float(disk_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU,内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU利用率过高' + "' where ip = '" + ip + "'")
                        elif (mem_percent) >= float(mem_threshold):
                            if float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    cpu_percent) < float(cpu_threshold):
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_mssql_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存利用率过高' + "' where ip = '" + ip + "'")
                        else:
                            get_mssql_conn().ExecUpdate(
                                "update " + tableName + " set is_normal = '0',err_info = '" + u'磁盘利用率过高' + "' where ip = '" + ip + "'")
                    else:
                        get_mssql_conn().ExecUpdate(
                            "update " + tableName + " set is_normal = '1',err_info = '" + u'CPU,内存及磁盘利用率正常' + "' where ip = '" + ip + "'")
        else:
            print u"查询" + tableName + u"失败"
    except:
        traceback.print_exc()
    finally:
        pass

#设置日志级别
def logging_level():
    logging_level = get_config().get("logging", "logging_level")
    if logging_level == 50:
        return logging.CRITICAL
    elif logging_level == 40:
        return logging.ERROR
    elif logging_level == 30:
        return logging.WARNING
    elif logging_level == 20:
        return logging.INFO
    elif logging_level == 10:
        return logging.DEBUG
    else:
        return logging.NOTSET


def oracle_monitor(ip,xtid,cpu_percent,mem_percent,disk,cur_time,cpu_threshold,mem_threshold,disk_threshold,length):
    try:
        for i in range(length):
            if i == 0:
                disk_usage_max = disk[i]
            else:
                if disk_usage_max[1] < disk[i][1]:
                    disk_usage_max = disk[i]
        user = get_config().get("oracle_info","user")
        db = get_config().get("oracle_info", "db")
        tableName = get_config().get("oracle_info", "tableName")
        table_exists = get_oracle_conn().ExecQuery(
            "select COUNT(1) from user_tables where table_name = upper('" + tableName + "')")
        if table_exists:
            if table_exists[0][0] == 0:
                create_table = "CREATE TABLE " + tableName + "" \
                                                             "(" \
                                                             "XTID        INTEGER not null," \
                                                             "CPU_PERCENT FLOAT,DISK_NAME   VARCHAR2(50)," \
                                                             "DISK_USAGE  FLOAT," \
                                                             "MEM_PERCENT FLOAT," \
                                                             "CUR_TIME    NVARCHAR2(50) not null," \
                                                             "IP          NCHAR(60) not null," \
                                                             "ERR_INFO    CLOB,IS_NORMAL   NCHAR(10)" \
                                                             ")"
                get_oracle_conn().ExecCreate_table(create_table)
                alter_table = "alter table " + tableName + " add constraint PK_XTID primary key (XTID)"
                get_oracle_conn().ExecCreate_table(alter_table)
                create_index = "create index "+ tableName +"_UNIQUE on " + tableName + " (XTID, IP)"
                get_oracle_conn().ExecCreate_table(create_index)
            else:
                resList = get_oracle_conn().ExecQuery(
                    "SELECT * FROM " + tableName + " where xtid = '" + xtid + "' and ip = '" + ip + "'")
                if not resList:
                    insert_str = get_insert_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip)
                    get_oracle_conn().ExecInsert(insert_str)
                    if float(cpu_percent) >= float(cpu_threshold) or float(mem_percent) >= float(
                            mem_threshold) or float(disk_usage_max[1]) >= float(disk_threshold):
                        if float(cpu_percent) > float(cpu_threshold):
                            if float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) < float(disk_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和内存利用率过高' + "' where ip = '" + ip + "'")
                            elif float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    mem_percent) < float(mem_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和磁盘利用率过高' + "' where ip = '" + ip + "'")
                            elif float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) >= float(disk_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU,内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU利用率过高' + "' where ip = '" + ip + "'")
                        elif (mem_percent) >= float(mem_threshold):
                            if float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    cpu_percent) < float(cpu_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存利用率过高' + "' where ip = '" + ip + "'")
                        else:
                            get_oracle_conn().ExecUpdate(
                                "update " + tableName + " set is_normal = '0',err_info = '" + u'磁盘利用率过高' + "' where ip = '" + ip + "'")
                    else:
                        get_oracle_conn().ExecUpdate(
                            "update " + tableName + " set is_normal = '1',err_info = '" + u'CPU,内存及磁盘利用率正常' + "' where ip = '" + ip + "'")
                else:
                    update_str = get_update_str(tableName,xtid,cpu_percent,disk_usage_max,mem_percent,cur_time,ip)
                    get_oracle_conn().ExecUpdate(update_str)
                    if float(cpu_percent) >= float(cpu_threshold) or float(mem_percent) >= float(
                            mem_threshold) or float(disk_usage_max[1]) >= float(disk_threshold):
                        if float(cpu_percent) > float(cpu_threshold):
                            if float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) < float(disk_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和内存利用率过高' + "' where ip = '" + ip + "'")
                            elif float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    mem_percent) < float(mem_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU和磁盘利用率过高' + "' where ip = '" + ip + "'")
                            elif float(mem_percent) >= float(mem_threshold) and float(
                                    disk_usage_max[1]) >= float(disk_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU,内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'CPU利用率过高' + "' where ip = '" + ip + "'")
                        elif (mem_percent) >= float(mem_threshold):
                            if float(disk_usage_max[1]) >= float(disk_threshold) and float(
                                    cpu_percent) < float(cpu_threshold):
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存及磁盘利用率过高' + "' where ip = '" + ip + "'")
                            else:
                                get_oracle_conn().ExecUpdate(
                                    "update " + tableName + " set is_normal = '0',err_info = '" + u'内存利用率过高' + "' where ip = '" + ip + "'")
                        else:
                            get_oracle_conn().ExecUpdate(
                                "update " + tableName + " set is_normal = '0',err_info = '" + u'磁盘利用率过高' + "' where ip = '" + ip + "'")
                    else:
                        get_mssql_conn().ExecUpdate(
                            "update " + tableName + " set is_normal = '1',err_info = '" + u'CPU,内存及磁盘利用率正常' + "' where ip = '" + ip + "'")
        else:
            print u"查询" + tableName + u"失败"
    except:
        traceback.print_exc()
    finally:
        pass

def main():
    try:
        # get_ip = get_ipaddr()
        db_id = get_config().get("db_id","dbid")
        ip = get_config().get("local_ip", "ip")
        xtid = get_config().get("system_id","xtid")
        if db_id == "":
            print u"请选择数据库类型"
            time.sleep(10)
        elif ip == "":
            print u"请配置本地IP地址"
            time.sleep(10)
        elif xtid == "":
            print u"请配置系统id"
            time.sleep(10)
        else:
            cpu_percent = system_info.get_cpu_info()
            mem_percent = system_info.get_memory_info()
            disk = system_info.get_disk_info()
            # system_info.get_sys_version()
            # ipaddress = system_info.get_ip()
            # print ('\n------------------------------------------------------------------------')
            # print('IPAddress\n------------------------------------------------------------------------')
            # for i in ipaddress:
            #     print "IP:%7s" % str(i)
            cur_time = time.strftime("%Y-%m-%d %H:%M:%S")
            length = len(disk)
            cpu_threshold = get_config().get("cpu", "cpu_threshold")
            mem_threshold = get_config().get("memory", "mem_threshold")
            disk_threshold = get_config().get("disk", "disk_threshold")
            db_id = get_config().get("db_id","dbid")
            if float(cpu_percent) >= float(cpu_threshold):
                time.sleep(1)
                cpu_percent_new = system_info.get_cpu_info()
                if float(cpu_percent_new) >= float(cpu_threshold) and float(cpu_percent) >= float(cpu_threshold):
                    if db_id == '1':
                        mssql_monitor(ip,xtid,cpu_percent,mem_percent,disk,cur_time,cpu_threshold,mem_threshold,disk_threshold,length)
                    else:
                        oracle_monitor(ip,xtid,cpu_percent,mem_percent,disk,cur_time,cpu_threshold,mem_threshold,disk_threshold,length)
            else:
                if db_id == '1':
                    mssql_monitor(ip, xtid, cpu_percent, mem_percent, disk, cur_time, cpu_threshold, mem_threshold,
                                    disk_threshold, length)
                else:
                    oracle_monitor(ip, xtid, cpu_percent, mem_percent, disk, cur_time, cpu_threshold, mem_threshold,
                                   disk_threshold, length)
    except:
        traceback.print_exc()
    finally:
        pass

if __name__ == '__main__':
    get_replace()
    get_mssql_conn()
    logname = 'sysMon.'+ time.strftime('%Y-%m-%d') + '.log'
    logging.basicConfig(level=logging_level())
    count = 1
    while 1:
        get_clear()
        start_time = time.strftime('%Y-%m-%d') + ' ' + get_config().get("time", "start_time")
        end_time = time.strftime('%Y-%m-%d') + ' ' + get_config().get("time", "end_time")
        if compare_time(start_time,end_time):
            main()
        else:
            count += 1
            print u"当前时间不运行"
            print u"running time: %s" % count
        interval = get_config().getfloat("time", "interval")
        time.sleep(interval)



