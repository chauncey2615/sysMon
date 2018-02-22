# -*- coding: utf-8 -*-
#encoding:utf-8
import cx_Oracle
import sys
import time
import traceback

class Oracle:
    """
        对cx_Oracle的简单封装
        cx_Oracle库，该库到这里下载：http://www.lfd.uci.edu/~gohlke/pythonlibs/#cx_Oracle
        使用该库时，需要在Sql Server Configuration Manager里面将TCP/IP协议开启
     """
    def __init__(self,host,port,user,pwd,db):
        self.host = host
        self.port = port
        self.user = user
        self.pwd = pwd
        self.db = db

    def __getConnect(self):
        """
        得到连接信息
        返回: conn.cursor()
        """
        if not self.db or not self.host or not self.port or not self.user or not self.pwd:
            print u"没有设置oracle数据库信息"
            time.sleep(10)
        else:
            try:
                #self.conn = cx_Oracle.connect(self.host,self.port,self.user,self.pwd,self.db,charset="utf8")
                self.conn = cx_Oracle.connect(self.user, self.pwd,self.host + "/" +self.db)
                cur = self.conn.cursor()
                return cur
            except:
                print u"连接数据库失败"
                traceback.print_exc()
                return False
            finally:
                pass
        # if not cur:
        #     raise (NameError,u"连接数据库失败")
        #     print traceback.print_exc()
        #     time.sleep(10)
        # else:
        #     return cur
        # try:
        #     cur = self.conn.cursor()
        # except:
        #     info = sys.exc_info()
        #     print info[0], ":", info[1]
        #     print u"数据库连接"
        # finally:
        #     return cur

    def ExecQuery(self,sql):
        """
                执行查询语句
                返回的是一个包含tuple的list，list的元素是记录行，tuple的元素是每行记录的字段

                调用示例：
                        ms = MSSQL(host="localhost",user="sa",pwd="123456",db="PythonWeiboStatistics")
                        resList = ms.ExecQuery("SELECT id,NickName FROM WeiBoUser")
                        for (id,NickName) in resList:
                            print str(id),NickName
        """
        cur = self.__getConnect()
        if cur:
            try:
                cur.execute(sql)
                resList = cur.fetchall()
                return  resList
            except:
                print u"查询失败"
                traceback.print_exc()
                return False
            finally:
                self.conn.close()
                pass

    def ExecInsert(self,sql):
        cur = self.__getConnect()
        if cur:
            try:
                cur.execute(sql)
                self.conn.commit()
            except:
                info = sys.exc_info()
                print info[0],":",info[1]
                self.conn.rollback()
                print u"Insert插入失败,回滚"
            finally:
                self.conn.close()

    def ExecUpdate(self, sql):
        cur = self.__getConnect()
        if cur:
            try:
                cur.execute(sql)
                self.conn.commit()
            except:
                info = sys.exc_info()
                print info[0], ":", info[1]
                self.conn.rollback()
                print u"Update失败,回滚"
            finally:
                self.conn.close()
                pass

    def ExecCreate_table(self,sql):
        cur = self.__getConnect()
        if cur:
            try:
                cur.execute(sql)
                self.conn.commit()
            except:
                info = sys.exc_info()
                print info[0], ":", info[1]
                self.conn.rollback()
                print u"创建表失败"
            finally:
                self.conn.close()
                pass