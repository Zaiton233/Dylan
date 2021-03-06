import datetime
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from ctypes import cdll
from ctypes.wintypes import DWORD, HWND

import psutil
import PyQt5
import requests
from flask import Flask, request
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, Qt, QUrl, pyqtSlot
from PyQt5.QtGui import QColor, QCursor, QFont, QIcon, QPalette, QPixmap
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtWidgets import *

from acrylicGui import Menu
from betterLog import *
from command import *
from gui import Ui_Form
from reg import *
from server import Server
from task import *


class splash(QSplashScreen):
  '''启动页面'''
  def mousePressEvent(self, event):
    pass

class gui(QWidget,Ui_Form):
  '''主窗口'''
  def __init__(self, parent=None):
    '''主窗口设置'''
    super(gui, self).__init__(parent)
    self.setupUi(self)
    global forms
    channel.registerObject("obj", Function)
    self.setWindowTitle("Dylan "+VERSION)
    self.about_logo.setText(" Dylan Alpha")
    self.tabWidget.setCurrentIndex(0)
    self.Panel_input.setDisabled(True)
    self.Panel_start.setDisabled(False)
    self.Panel_restart.setDisabled(True)
    self.Panel_stop.setDisabled(True)
    self.Panel_forcestop.setDisabled(True)
    self.Bot_stop.setDisabled(True)
    self.pluginList.setSpacing(2)
    forms={
      "self":self,
      "bot":{
        "start":self.Bot_start,
        "stop":self.Bot_stop,
        "qq":self.Bot_qq_2,
        "state":self.Bot_state_2,
        "receive":self.Bot_receive_2,
        "send":self.Bot_send_2,
      },
      "panel":{
        "console":self.Panel_console,
        "input":self.Panel_input,
        "start":self.Panel_start,
        "stop":self.Panel_stop,
        "restart":self.Panel_restart,
        "forcestop":self.Panel_forcestop,
        "state":self.Panel_state_2,
        "version":self.Panel_version_2,
        "gamemode":self.Panel_gamemode_2,
        "difficulty":self.Panel_difficulty_2,
        "levelname":self.Panel_levelname_2,
        "port":self.Panel_port_2,
        "ram":self.Panel_ram_2,
        "cpu":self.Panel_cpu_2
      },
      "setting":{
        "start":{
          "selectfile":self.setting_selectfile,
          "filepath":self.setting_filepath,
          "autoRestart":self.setting_autoRestart
        },
        "bot":{
          "logout":self.setting_logout,
          "enableOutputMsgToLog":self.setting_enableOutputMsgToLog,
          "sendPort":self.setting_sendPort,
          "listenPort":self.setting_listenPort,
          "botFilepath":self.setting_botFilepath
        },
        "console":{
          "colorfulLogOut":self.setting_colorfulLogOut,
          "enableOutputToLog":self.setting_enableOutputToLog,
          "outputCommandToConsole":self.setting_outputCommandToConsole
        },
        "msg":{
          "groupList":self.setting_groupList,
          "permissionList":self.setting_permissionList,
          "givePermissionToAllAdmin":self.setting_givePermissionToAllAdmin
        },
        "Dylan":{
          "enableUpdate":self.setting_enableUpdate,
          "enableAnnouncement":self.setting_enableAnnouncement,
          "chosenTheme":self.setting_chosenTheme,
        }
      },
      "regularlist":self.regularlist,
      "timedTask":{
        "timedTaskList":self.timedTaskList,
        "timedTask_state":self.timedTask_state
        }
      }
    self.loadSetting()
    self.loadRegular()
    self.loadPlugins()
    self.loadTimedTask()
    self.connectFunctions()
    self.checkRegular()
    self.checkTask()

  def showEvent(self, event):
    '''启动时加载更新信息与初始化'''
    self.resizeConsole()
    msgbox=QMessageBox(self)
    text=None
    failTimes=0
    try:
      enableUpdate=settings["Dylan"]["enableUpdate"]
    except:
      enableUpdate=True
    while enableUpdate:
      try:
        if failTimes<=3:
          versionJson=json.loads(requests.request(method="GET",url="https://api.github.com/repos/Zaiton233/Dylan/releases").text)
          if int(re.findall("(\d{8})",versionJson[0]["name"])[0])<=int(re.findall("(\d{8})",VERSION)[0]):
            break
          if not versionJson[0]["draft"]:
            body=versionJson[0]["body"].replace("\r","").replace("\n","<br>")
            text=f'<div>当前版本：{VERSION}</div><div>最新版本：{versionJson[0]["name"]}</div><div>发布日期：{versionJson[0]["published_at"]}</div><div>下载链接：<br><a href="{versionJson[0]["html_url"]}" style="color:#2d94a7;">{versionJson[0]["html_url"]}</a><hr></div><div style="word-break: break-all;">更新说明：<br>{body}</div>'
            msgbox.setWindowTitle("Dylan - 发现新版本")
            msgbox.setText(text)
            msgbox.show()
            break
          else:
            break
        else:
          break
      except Exception as e:
        pass
      finally:
        failTimes+=1

  def loadSetting(self):
    '''加载设置'''
    settingList=forms["setting"]
    for group in settingList:
      for object in settingList[group]:
        try:
          if type(settings[group][object])==bool:
            if "setChecked" in dir(settingList[group][object]):
              settingList[group][object].setChecked(settings[group][object])
          elif type(settings[group][object])==int:
            if "setValue" in dir(settingList[group][object]):
              settingList[group][object].setValue(settings[group][object])
            elif "setCurrentIndex" in dir(settingList[group][object]):
              settingList[group][object].setCurrentIndex(settings[group][object])
          elif type(settings[group][object])==str:
            if "setText" in dir(settingList[group][object]):
              settingList[group][object].setText(settings[group][object])
          elif type(settings[group][object])==list:
            if "setPlainText" in dir(settingList[group][object]):
              text=""
              for i in settings[group][object]:
                text=text+str(i)+"\n"
              settingList[group][object].setPlainText(text)
        except:
          pass
    global sendPort,listenPort
    listenPort=self.setting_listenPort.value()
    sendPort=self.setting_sendPort.value()
    self.setThemes(self.setting_chosenTheme.currentIndex())

  def loadPlugins(self):
    '''加载插件'''
    self.pluginList.clear()
    self.pluginsPath=None
    if settings.get("start")==None:
      pass
    elif settings["start"].get("filepath")==None:
      pass
    elif os.path.exists(settings["start"]["filepath"]):
      if os.path.exists(os.path.join(os.path.split(settings["start"]["filepath"])[0],"plugins")):
        self.pluginsPath=os.path.join(os.path.split(settings["start"]["filepath"])[0],"plugins")
      elif os.path.exists(os.path.join(os.path.split(settings["start"]["filepath"])[0],"plugin")):
        self.pluginsPath=os.path.join(os.path.split(settings["start"]["filepath"])[0],"plugin")
      else:
        self.pluginsPath=None
      if self.pluginsPath!=None:
        total=0
        enabled=0
        disabled=0
        time.sleep(0.05)
        font = QFont()
        font.setFamily("宋体")
        font.setPointSize(10)
        for f in os.listdir(self.pluginsPath):
          if f.endswith((".dll",".js",".lua",".py",".jar")):
            total+=1
            enabled+=1
            font.setItalic(False)
            item = QtWidgets.QListWidgetItem()
            item.setText(f)
            item.setFont(font)
            self.pluginList.addItem(item)
          elif f[:-2].endswith((".dll",".js",".lua",".py",".jar")) and f[-2:]==".d":
            total+=1
            disabled+=1
            font.setItalic(True)
            item = QtWidgets.QListWidgetItem()
            item.setText("*已禁用 "+f[:-2])
            item.setFont(font)
            self.pluginList.addItem(item)
        self.plugins_total.setText(f"共{total}个插件，其中{enabled}个已启用，{disabled}个已禁用")

  def setHtml(self,theme):
    '''设置控制台主题'''
    self.Panel_console.load(QUrl("file:///"+str(consolePath).replace('\\',"/")+f"?type=bds&theme={theme}"))
    self.Panel_console.page().setWebChannel(channel)
    self.Bot_console.load(QUrl("file:///"+str(consolePath).replace('\\',"/")+f"?type=bot&theme={theme}"))
    self.Bot_console.page().setWebChannel(channel)

  def connectFunctions(self):
    '''连接组件与函数'''
    self.regularlist.itemChanged.connect(self.checkRegular)
    self.regularlist.itemClicked.connect(self.checkRegular)
    self.timedTaskList.itemChanged.connect(self.checkTask)
    self.timedTaskList.itemClicked.connect(self.checkTask)
    self.timedTaskList.customContextMenuRequested.connect(self.createTimedTaskMenu)
    self.pluginList.customContextMenuRequested.connect(self.createPluginMenu)
    self.regularlist.customContextMenuRequested.connect(self.createRegularMenu)
    self.setting_selectfile.clicked.connect(lambda: self.selectFile(0))
    self.setting_logout.clicked.connect(lambda: self.botControl(3))
    self.setting_botSelectfile.clicked.connect(lambda: self.selectFile(1))
    self.setting_reset.clicked.connect(self.reset)
    self.setting_savePort.clicked.connect(lambda:self.savePort())
    self.Panel_start.clicked.connect(lambda: self.serverControl(1))
    self.Panel_stop.clicked.connect(lambda: self.serverControl(2))
    self.Panel_restart.clicked.connect(lambda: self.serverControl(3))
    self.Panel_forcestop.clicked.connect(lambda: self.serverControl(4))
    self.Bot_start.clicked.connect(lambda: self.botControl(1))
    self.Bot_stop.clicked.connect(lambda: self.botControl(2))
    self.Panel_input.returnPressed.connect(self.transferCommand)
    self.tabWidget.currentChanged.connect(self.resizeConsole)

  def createPluginMenu(self,pos):
    '''创建插件管理菜单'''
    row = self.pluginList.currentRow()
    if self.themeId==3:
      self.pluginMenu = Menu(parent=self.pluginList)
    else:
      self.pluginMenu = QMenu(parent=self.pluginList)
    self.addPlugin = QAction('导入插件',self.pluginList)
    self.pluginMenu.addAction(self.addPlugin)
    self.removePlugin = QAction('删除插件',self.pluginList)
    self.pluginMenu.addAction(self.removePlugin)
    if self.pluginList.itemAt(pos)!=None:
      if self.pluginList.itemAt(pos).text()[0]=="*":
        self.disablePlugin = QAction('启用插件',self.pluginList)
      else:
        self.disablePlugin = QAction('禁用插件',self.pluginList)
    else:
      self.disablePlugin = QAction('禁用插件',self.pluginList)
    self.pluginMenu.addAction(self.disablePlugin)
    self.pluginMenu.addSeparator()
    self.refreshPlugin = QAction('刷新',self.pluginList)
    self.pluginMenu.addAction(self.refreshPlugin)
    if row==-1 or self.pluginList.itemAt(pos)==None:
      self.removePlugin.setDisabled(True)
      self.disablePlugin.setDisabled(True)
    if server.isRunning() or self.pluginsPath==None:
      self.removePlugin.setDisabled(True)
      self.disablePlugin.setDisabled(True)
      self.addPlugin.setDisabled(True)
    self.addPlugin.triggered.connect(lambda: self.pluginManagement(1))
    self.removePlugin.triggered.connect(lambda: self.pluginManagement(2,self.pluginList.itemAt(pos)))
    self.refreshPlugin.triggered.connect(lambda: self.loadPlugins())
    self.disablePlugin.triggered.connect(lambda: self.pluginManagement(3,self.pluginList.itemAt(pos)))
    time.sleep(0.1)
    self.pluginMenu.popup(QCursor.pos())

  def pluginManagement(self,type,item=None):
    '''插件管理'''
    if type==1:
      importFile=QFileDialog.getOpenFileName(self, "选择文件",self.pluginsPath, "插件 (*.dll *.js *.lua *.py *.jar)")
      if importFile[0]!='':
        try:
          shutil.copyfile(importFile[0], os.path.join(self.pluginsPath,os.path.split(importFile[0])[1]))
          QMessageBox.information(
            self,
            "Dylan",
            f"导入成功",
            QMessageBox.Yes
          )
        except Exception as e:
          QMessageBox.information(
            self,
            "Dylan",
            f"导入失败\n{e}",
            QMessageBox.Yes
          )
        self.loadPlugins()
    elif type==2 and self.pluginsPath!=None:
      if item.text()[0]=="*":
        fileName=item.text()[5:]
      else:
        fileName=item.text()
      reply = QMessageBox.warning(
      self,
      'Dylan',
      f'确定删除"{fileName}"？\n他将会永远失去！（真的很久！）',
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No
      )
      if reply == QMessageBox.Yes:
        try:
          if item.text()[0]=="*":
            os.remove(os.path.join(self.pluginsPath,fileName+".d"))
          else:
            os.remove(os.path.join(self.pluginsPath,item.text()))
          QMessageBox.information(
            self,
            "Dylan",
            "删除成功",
            QMessageBox.Yes
          )
        except Exception as e:
          QMessageBox.information(
            self,
            "Dylan",
            f"删除失败\n{e}",
            QMessageBox.Yes
          )
        self.loadPlugins()
    elif type==3:
      try:
        if item.text()[0]=="*":
          os.rename(
            os.path.join(self.pluginsPath,item.text()[5:]+".d"),
            os.path.join(self.pluginsPath,item.text()[5:])
          )
        else:
          os.rename(
            os.path.join(self.pluginsPath,item.text()),
            os.path.join(self.pluginsPath,item.text()+".d")
          )
      except Exception as e:
        QMessageBox.information(
            self,
            "Dylan",
            f"插件状态更改失败\n{e}",
            QMessageBox.Yes
          )
    self.loadPlugins()

  def createTimedTaskMenu(self,pos):
    '''创建定时任务菜单'''
    item = self.timedTaskList.indexAt(pos)
    row=item.row()
    if self.themeId==3:
      self.timedTaskMenu = Menu(parent=self.timedTaskList)
    else:
      self.timedTaskMenu = QMenu(parent=self.timedTaskList)
    self.addTask = QAction('添加任务',self.timedTaskList)
    self.timedTaskMenu.addAction(self.addTask)
    self.removeTask = QAction('删除任务',self.timedTaskList)
    self.timedTaskMenu.addAction(self.removeTask)
    self.removeAllTask = QAction('清空任务',self.timedTaskList)
    self.timedTaskMenu.addAction(self.removeAllTask)
    self.timedTaskMenu.addSeparator()
    self.refreshTask = QAction('刷新',self.timedTaskList)
    self.timedTaskMenu.addAction(self.refreshTask)
    if row==-1:
      self.removeTask.setDisabled(True)
    if self.timedTaskList.rowCount()<=0:
      self.removeAllTask.setDisabled(True)
    self.addTask.triggered.connect(lambda: self.addTimedTask())
    self.removeTask.triggered.connect(lambda: self.removeTimedTask(row))
    self.refreshTask.triggered.connect(lambda: self.reloadTimedTask())
    self.removeAllTask.triggered.connect(lambda: self.removeAllTimedTask())
    self.timedTaskMenu.popup(QCursor.pos())

  def addTimedTask(self):
    '''新增定时任务'''
    self.timedTaskList.insertRow(0)
    typeBox=QComboBox()
    typeBox.addItems(["禁用","时间间隔","Cron表达式"])
    self.timedTaskList.setCellWidget(0, 1, typeBox)

  def removeTimedTask(self,row=-1):
    '''删除定时任务'''
    if row<0:
      return False
    reply = QMessageBox.warning(
    self,
    'Dylan',
    f"确定要删除第{row+1}行吗？\n第{row+1}行将会永远失去！（真的很久！）",
    QMessageBox.Yes | QMessageBox.No,
    QMessageBox.No
    )
    if reply == QMessageBox.Yes:
      self.timedTaskList.removeRow(row)

  def removeAllTimedTask(self):
    '''清空定时任务'''
    reply = QMessageBox.warning(
      self,
      'Dylan',
      "确定要清空定时任务吗？\n他们将会永远失去！（真的很久！）",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No
      )
    if reply == QMessageBox.Yes:
      for i in range(self.timedTaskList.rowCount()):
        self.timedTaskList.removeRow(0)

  def reloadTimedTask(self):
    '''刷新定时任务'''
    for i in range(self.timedTaskList.rowCount()):
      self.timedTaskList.removeRow(0)
    self.loadTimedTask()

  def loadTimedTask(self):
    '''加载定时任务'''
    for i in datas:
      if i=="taskList":
        for task in list(datas["taskList"].keys()):
          try:
            self.timedTaskList.insertRow(0)
            typeBox=QComboBox()
            typeBox.addItems(["禁用","时间间隔","Cron表达式"])
            typeBox.setCurrentIndex(datas["taskList"][task]["type"])
            self.timedTaskList.setItem(0,0,QTableWidgetItem(datas["taskList"][task]["name"]))
            self.timedTaskList.setCellWidget(0, 1, typeBox)
            self.timedTaskList.setItem(0,2,QTableWidgetItem(datas["taskList"][task]["value"]))
            self.timedTaskList.setItem(0,3,QTableWidgetItem(datas["taskList"][task]["remark"]))
            self.timedTaskList.setItem(0,4,QTableWidgetItem(datas["taskList"][task]["command"]))
          except:
            pass

  def checkTask(self):
    '''检查定时任务语法'''
    name=[]
    for singleRow in range(self.timedTaskList.rowCount()):
      if self.timedTaskList.item(singleRow,0)==None:
        pass
      elif self.timedTaskList.item(singleRow,0).text() in name:
        self.timedTaskList.item(singleRow,0).setBackground(QColor(255,0,0,40))
      else:
        name.append(self.timedTaskList.item(singleRow,0).text())
        self.timedTaskList.item(singleRow,0).setBackground((QColor(0,0,0,0)))
      if self.timedTaskList.cellWidget(singleRow,1).currentIndex()==2:
        try:
          if self.timedTaskList.item(singleRow,2)!=None:
            if self.timedTaskList.item(singleRow,2).text()=="":
              continue
            CronTab(self.timedTaskList.item(singleRow,2).text()).next(default_utc=False)
          self.timedTaskList.item(singleRow,2).setBackground((QColor(0,0,0,0)))
        except:
          self.timedTaskList.item(singleRow,2).setBackground(QColor(255,0,0,40))
      elif self.timedTaskList.cellWidget(singleRow,1).currentIndex()==1 and self.timedTaskList.item(singleRow,2)!=None:
        if re.search("^[\d]{0,}\.?[\d]{1,}$",self.timedTaskList.item(singleRow,2).text()):
          self.timedTaskList.item(singleRow,2).setBackground((QColor(0,0,0,0)))
        else:
          self.timedTaskList.item(singleRow,2).setBackground(QColor(255,0,0,40))

  def createRegularMenu(self,pos):
    '''创建正则管理页面的右键菜单'''
    item = self.regularlist.indexAt(pos)
    row=item.row()
    if self.themeId==3:
      self.regularMenu = Menu(parent=self.regularlist)
    else:
      self.regularMenu = QMenu(parent=self.regularlist)
    self.addRegular = QAction('添加记录',self.regularlist)
    self.regularMenu.addAction(self.addRegular)
    self.removeRegular = QAction('删除记录',self.regularlist)
    self.regularMenu.addAction(self.removeRegular)
    self.removeAllRegular = QAction('清空记录',self.regularlist)
    self.regularMenu.addAction(self.removeAllRegular)
    self.regularMenu.addSeparator()
    self.refreshRegular = QAction('刷新',self.regularlist)
    self.regularMenu.addAction(self.refreshRegular)
    if row==-1:
      self.removeRegular.setDisabled(True)
    if self.regularlist.rowCount()<=0:
      self.removeAllRegular.setDisabled(True)
    self.addRegular.triggered.connect(lambda: self.regularManagement(1))
    self.removeRegular.triggered.connect(lambda: self.regularManagement(2,row))
    self.refreshRegular.triggered.connect(lambda: self.reloadRegular())
    self.removeAllRegular.triggered.connect(lambda: self.removeAllReg())
    self.regularMenu.popup(QCursor.pos())

  def regularManagement(self,type,row=-1):
    '''正则管理'''
    if type==1:
      self.regularlist.insertRow(0)
      captureArea=QComboBox()
      captureArea.addItems(["禁用","私聊（管理）","私聊（所有）","群聊（管理）","群聊（所有）","控制台"])
      self.regularlist.setCellWidget(0, 0, captureArea)
    elif type==2 and row!=-1:
      reply = QMessageBox.warning(
      self,
      'Dylan',
      f"确定要删除第{row+1}行吗？\n第{row+1}行将会永远失去！（真的很久！）",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No
      )
      if reply == QMessageBox.Yes:
        self.regularlist.removeRow(row)

  def checkRegular(self):
    '''检查正则表达式语法'''
    for singleRow in range(self.regularlist.rowCount()):
      try:
        if self.regularlist.item(singleRow,1)==None:
          continue
        re.findall(self.regularlist.item(singleRow,1).text(),"test")
        self.regularlist.item(singleRow,1).setBackground((QColor(0,0,0,0)))
      except:
        self.regularlist.item(singleRow,1).setBackground(QColor(255,0,0,40))

  def addSingelRegular(self,type=str):
    '''读取时添加正则记录'''
    global regularList
    if regularList.get(type)==None:
      return False
    if type=="disabled":
      typeIndex=0
    elif type=="private_admin":
      typeIndex=1
    elif type=="private":
      typeIndex=2
    elif type=="group_admin":
      typeIndex=3
    elif type=="group":
      typeIndex=4
    elif type=="console":
      typeIndex=5
    for singleRegular in regularList[type]:
      try:
        self.regularlist.insertRow(0)
        captureArea=QComboBox()
        captureArea.addItems(["禁用","私聊（管理）","私聊（所有）","群聊（管理）","群聊（所有）","控制台"])
        captureArea.setCurrentIndex(typeIndex)
        self.regularlist.setCellWidget(0, 0, captureArea)
        self.regularlist.setItem(0,1,QTableWidgetItem(singleRegular["regular"]))
        self.regularlist.setItem(0,2,QTableWidgetItem(singleRegular["remark"]))
        self.regularlist.setItem(0,3,QTableWidgetItem(singleRegular["command"]))
      except:
        pass

  def loadRegular(self):
    '''加载正则记录'''
    self.addSingelRegular("group")
    self.addSingelRegular("group_admin")
    self.addSingelRegular("private")
    self.addSingelRegular("private_admin")
    self.addSingelRegular("disabled")
    self.addSingelRegular("console")

  def removeAllReg(self):
    '''删除所有正则记录'''
    reply = QMessageBox.warning(
      self,
      'Dylan',
      "确定要清空所有记录吗？\n他们将会永远失去！（真的很久！）",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No
      )
    if reply == QMessageBox.Yes:
      for i in range(self.regularlist.rowCount()):
        self.regularlist.removeRow(0)

  def reloadRegular(self):
    '''重载正则记录'''
    for i in range(self.regularlist.rowCount()):
      self.regularlist.removeRow(0)
    self.loadRegular()

  def savePort(self):
    '''保存端口'''
    global sendPort,listenPort
    if listenPort!=self.setting_listenPort.value():
      info="已保存\n（接收端口将在下一次启动后生效）"
      listenPort=self.setting_listenPort.value()
    else:
      if sendPort!=self.setting_sendPort.value():
        sendPort=self.setting_sendPort.value()
      info="已保存"
    QMessageBox.information(
      self,
      "Dylan",
      info,
      QMessageBox.Yes
    )

  def reset(self):
    '''重置设置'''
    global stopSavingSetting,selfPath
    reply = QMessageBox.warning(
      self,
      'Dylan',
      "确定重置所有设置吗？\n他们将会永远失去！（真的很久！）\n\n确定重置后将自动退出程序，默认设置将在下一次启动时应用",
      QMessageBox.Yes | QMessageBox.No,
      QMessageBox.No
      )
    if reply == QMessageBox.Yes:
      if server.isRunning():
        QMessageBox.information(
          self,
          "Dylan",
          "服务器未关闭，重置已取消",
          QMessageBox.Yes
        )
      else:
        stopSavingSetting=True
        MainWindow.setDisabled(True)
        closeBot()
        time.sleep(1)
        with open(os.path.join(selfPath,"setting.json"), 'w',encoding='utf-8') as jsonFile:
          jsonFile.write("{}")
        sys.exit()

  def setThemes(self,themeId):
    '''设置主题'''
    self.themeId=themeId
    if themeId==0:
      self.setting_scrollArea.setStyleSheet(
        "#setting_scrollAreaWidgetContents{background:rgb(255,255,255);}")
      self.setHtml("default")
    elif themeId==1:
      qApp.setStyle("Fusion")
      self.setting_scrollArea.setStyleSheet(
        "#setting_scrollAreaWidgetContents{background:rgb(252,252,252);}")
      self.setHtml("fusion")
    elif themeId==2:
      qApp.setStyle("Fusion")
      dark_palette = QPalette()
      dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
      dark_palette.setColor(QPalette.WindowText, QColor(255,255,255))
      dark_palette.setColor(QPalette.Base, QColor(25, 25, 25))
      dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
      dark_palette.setColor(QPalette.ToolTipBase, QColor(255,255,255))
      dark_palette.setColor(QPalette.ToolTipText, QColor(255,255,255))
      dark_palette.setColor(QPalette.Text, QColor(255,255,255))
      dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
      dark_palette.setColor(QPalette.Disabled,QPalette.Button, QColor(30,30,30))
      dark_palette.setColor(QPalette.Disabled,QPalette.Text, QColor(100,100,100))
      dark_palette.setColor(QPalette.ButtonText, QColor(255,255,255))
      dark_palette.setColor(QPalette.BrightText, QColor(255,0,0))
      dark_palette.setColor(QPalette.Shadow, QColor(0,0,0,0))
      dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
      dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
      dark_palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
      dark_palette.setColor(QPalette.Disabled,QPalette.ButtonText, QColor(100,100,100))
      dark_palette.setColor(QPalette.Disabled,QPalette.Text, QColor(100,100,100))
      dark_palette.setColor(QPalette.Disabled,QPalette.ToolTipText, QColor(100,100,100))
      dark_palette.setColor(QPalette.Disabled,QPalette.ToolTipBase, QColor(100,100,100))
      dark_palette.setColor(QPalette.Disabled,QPalette.WindowText, QColor(100,100,100))
      qApp.setPalette(dark_palette)
      qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
      self.setHtml("fusion_dark")
    elif themeId==3:
      self.pluginList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.regularlist.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.timedTaskList.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.setting_scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
      self.setHtml("fusion")
      self.setting_scrollArea.setStyleSheet(
        "#setting_scrollAreaWidgetContents{background-color: transparent;}")
      self.setStyleSheet(
        """
        #setting_scrollAreaWidgetContents{background-color: transparent;}
        QScrollArea{background-color: transparent;}
        QMessageBox {
          border:0px solid #00000000;
          background-color: #F2F2F2;
        }
        QMessageBox QLabel#qt_msgbox_label {
          color: #000;
        }
      """)
      self.tabWidget.setStyleSheet(
        "QMenu{background:#fff} QTabWidget::pane{border: 1px;border-color:red;background-color: transparent;} QTabBar::tab {background-color: transparent;}QTabBar::tab:hover{background-color:#aaaaaa50}QTabBar::tab:selected{background-color: #33333350;}")
      self.setAttribute(Qt.WA_TranslucentBackground)
      self.setAttribute(Qt.WA_NoSystemBackground)
      hWnd = HWND(int(self.winId()))
      gradientColor = DWORD(0xC0F2F2F2)
      cdll.LoadLibrary('attachment/acrylic.dll').setBlur(hWnd, gradientColor)
    elif themeId==4:
      qApp.setStyle("Fusion")
      areo_palette = QPalette()
      areo_palette.setColor(QPalette.Window, QColor(53, 53, 53))
      areo_palette.setColor(QPalette.WindowText, QColor(255,255,255))
      areo_palette.setColor(QPalette.Base, QColor(25, 25, 25))
      areo_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
      areo_palette.setColor(QPalette.ToolTipBase, QColor(255,255,255))
      areo_palette.setColor(QPalette.ToolTipText, QColor(255,255,255))
      areo_palette.setColor(QPalette.Text, QColor(255,255,255))
      areo_palette.setColor(QPalette.Button, QColor(53, 53, 53))
      areo_palette.setColor(QPalette.Disabled,QPalette.Button, QColor(30,30,30))
      areo_palette.setColor(QPalette.Disabled,QPalette.Text, QColor(100,100,100))
      areo_palette.setColor(QPalette.ButtonText, QColor(255,255,255))
      areo_palette.setColor(QPalette.BrightText, QColor(255,0,0))
      areo_palette.setColor(QPalette.Shadow, QColor(0,0,0,0))
      areo_palette.setColor(QPalette.Link, QColor(42, 130, 218))
      areo_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
      areo_palette.setColor(QPalette.HighlightedText, QColor(0,0,0))
      areo_palette.setColor(QPalette.Disabled,QPalette.ButtonText, QColor(100,100,100))
      areo_palette.setColor(QPalette.Disabled,QPalette.Text, QColor(100,100,100))
      areo_palette.setColor(QPalette.Disabled,QPalette.ToolTipText, QColor(100,100,100))
      areo_palette.setColor(QPalette.Disabled,QPalette.ToolTipBase, QColor(100,100,100))
      areo_palette.setColor(QPalette.Disabled,QPalette.WindowText, QColor(100,100,100))
      qApp.setPalette(areo_palette)
      qApp.setStyleSheet("QToolTip { color: #ffffff; background-color: #2a82da; border: 1px solid white; }")
      self.setHtml("fusion_dark")
      self.setStyleSheet(
        "background-color: transparent;")
      self.tabWidget.setStyleSheet(
        "QTabWidget::pane{border: 1px;border-color:red;background-color: transparent;} QTabBar::tab {background-color: transparent;}QTabBar::tab:hover{background-color:#aaaaaa50}QTabBar::tab:selected{background-color: #33333350;}")
      self.setting_scrollArea.setStyleSheet(
        "scrollAreaWidgetContents{\nbackground:background:rgba(0,0,0,0);}")
      for child in self.findChildren(QPushButton):
        child.setStyleSheet("""QPushButton{
          border:1px solid #EEE;
          padding:5px;
          min-height:13px;
          border-radius:3px;
        }
        QPushButton:hover{
          border:1px solid #aaa;
        }
        QPushButton:disabled
        {
          border:1px solid #646464;
        }""")
      for child in self.findChildren((QTableView,QTableWidget,QComboBox)):
        child.setStyleSheet('''
        QComboBox{
          border-radius:3px;
          color:rgb(255,255,255);
          border:1px solid #EEE;
          padding: 2px;
        }
        QComboBox:disabled
        {
          border:1px solid #646464;
        }
        QComboBox:hover
        {
          border:1px solid #aaa;
        }
        QComboBox:on
        {
          border-radius:3px;
          background-color:#222;
        }
        QComboBox QAbstractItemView
        {
          border-radius:3px;
          outline: 0px solid gray;
          border:1px solid #EEE;
          color: rgb(255,255,255);
          background-color: rgb(45,45,45);
          selection-background-color: rgb(90,90,90);
        }
        QComboBox QAbstractItemView::item
        {
          height: 25px;
        }''')
      for child in self.findChildren(QCheckBox):
        child.setStyleSheet("""
        QCheckBox::indicator:unchecked
        {
          border:1px solid #EEE;
        }
        QCheckBox::indicator:unchecked:hover
        {
          border:1px solid #aaa;
        }
        QCheckBox::indicator:unchecked:pressed
        {
          border:1px solid #777;
        }
        QCheckBox::indicator:checked
        {
          border:1px solid #EEE;
          background-image:url(./attachment/check.png)
        }
        QCheckBox::indicator:checked:hover {
          border:1px solid #aaa;
        }
        QCheckBox::indicator:checked:pressed {
          border:1px solid #777;
        }
        """)
      for child in self.findChildren((QLineEdit,QTextEdit,QPlainTextEdit,QSpinBox)):
        child.setStyleSheet("""
        *{
          border:1px solid #EEE;
          border-radius:3px;
        }
        *:hover{
          border:1px solid #aaa;
        }
        *:disabled{
          border:1px solid #646464;
        }  """)
      for child in self.findChildren((QTableView,QTableWidget,QHeaderView)):
        child.setStyleSheet('''
        QTableView{
          border: 1px solid #eee;
          gridline-color:#aaa;
          selection-background-color: #ffffff10;
        }

        QHeaderView::section{
          background: transparent;
        }''')
      for child in self.findChildren((QListView,QListWidget)):
        child.setStyleSheet('''border: 1px solid #eee;''')
      self.setAttribute(Qt.WA_TranslucentBackground)
      cdll.LoadLibrary('./attachment/aeroDll.dll').setBlur(HWND(int(self.winId())))

  def transferCommand(self):
    '''转发输入命令'''
    text=self.Panel_input.text()
    server.outputCommand(text)
    self.Panel_input.setText("")

  def serverControl(self,type):
    '''服务器控制按钮'''
    global commandQueue,settings
    if type==1 and not server.isRunning() and not server.isWaitingRestart():
      while not commandQueue.empty():
        commandQueue.get()
      if not os.path.exists(self.setting_filepath.text()):
        QMessageBox.information(
          self,
          "Dylan",
          "启动文件不存在",
          QMessageBox.Yes
        )
      else:
        server.start()
        self.Panel_start.setDisabled(True)
        self.Panel_stop.setDisabled(False)
        self.Panel_input.setDisabled(False)
        self.Panel_forcestop.setDisabled(False)
        self.Panel_restart.setDisabled(False)
    elif type==2:
      server.changeRestart(False)
      server.outputCommand("stop")
    elif type==3:
      server.changeRestart(True)
      server.outputCommand("stop")
    elif type==4:
      reply = QMessageBox.warning(
        self,
        'Dylan',
        "确定要强制结束进程吗？\n可能导致存档丢失等问题",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
        )
      if server.isRunning() and reply == QMessageBox.Yes:
        try:
          server.forceStop()
        except Exception as e:
          QMessageBox.information(
            self,
            "Dylan",
            f"强制结束进程失败\n{e}",
            QMessageBox.Yes
          )

  def botControl(self,type):
    '''bot控制'''
    global botState,botProcess
    if type==1:
      if os.path.exists(settings["bot"]["botFilepath"]):
        botState=1
        botQueue.put("#cls")
        self.setting_savePort.setDisabled(True)
        self.setting_logout.setDisabled(True)
        self.Bot_start.setDisabled(True)
        self.Bot_stop.setDisabled(False)
        self.setting_sendPort.setDisabled(True)
        self.setting_listenPort.setDisabled(True)
        self.setting_botSelectfile.setDisabled(True)
        self.setting_botFilepath.setDisabled(True)
      else:
        QMessageBox.information(
          self,
          "Dylan",
          "启动文件不存在",
          QMessageBox.Yes
        )
    elif type==2 and botState==1:
      closeBot()
      time.sleep(0.1)
      global qq
      botQueue.put("<br>[<span style='color:#007ACC'>Dylan</span>]机器人已关闭")
      qq=0
      self.Bot_qq_2.setText("-")
      self.Bot_receive_2.setText("0")
      self.Bot_send_2.setText("0")
      self.Bot_state_2.setText("未启动")
      self.Bot_start.setDisabled(False)
      self.Bot_stop.setDisabled(True)
      self.setting_savePort.setDisabled(False)
      self.setting_logout.setDisabled(False)
      self.setting_sendPort.setDisabled(False)
      self.setting_listenPort.setDisabled(False)
      self.setting_botSelectfile.setDisabled(False)
      self.setting_botFilepath.setDisabled(False)
      botState=0
    elif type==3 and botState!=1:
      botFilepath=os.path.split(settings["bot"]["botFilepath"])[0]
      if os.path.exists(os.path.join(botFilepath,"device.json")):
        os.remove(os.path.join(botFilepath,"device.json"))
      if os.path.exists(os.path.join(botFilepath,"session.token")):
        os.remove(os.path.join(botFilepath,"session.token"))
      try:
        shutil.rmtree(os.path.join(botFilepath,"data"))
      except:
        pass
      try:
        shutil.rmtree(os.path.join(botFilepath,"logs"))
      except:
        pass
      QMessageBox.information(
      self,
      "Dylan",
      "删除成功！",
      QMessageBox.Yes
      )

  def selectFile(self,area=int):
    '''选择启动文件'''
    if area==0:
      startFile=QFileDialog.getOpenFileName(self, "选择文件",selfPath, "启动文件 (*.exe *.bat *.cmd)")
      if startFile[0]!='':
        self.setting_filepath.setText(startFile[0])
      self.loadPlugins()
    elif area==1:
      startFile=QFileDialog.getOpenFileName(self, "选择文件",selfPath, "go-cqhttp (go-cqhttp.exe go-cqhttp_windows_armv7.exe go-cqhttp_windows_386.exe go-cqhttp_windows_arm64.exe go-cqhttp_windows_amd64.exe)")
      if startFile[0]!='':
        self.setting_botFilepath.setText(startFile[0])

  def resizeConsole(self):
    '''自动调整控制台窗口大小'''
    global logQueue,botQueue
    logQueue.put(f"#size{str(self.Panel_console.width()-2)},{str(self.Panel_console.height()-2)}")
    botQueue.put(f"#size{str(self.Bot_console.width()-2)},{str(self.Bot_console.height()-2)}")

  def closeEvent(self, event):
    '''关闭事件'''
    if server.isRunning() or server.isWaitingRestart():
      event.ignore()
      QMessageBox.information(self,
        "Dylan",
        "服务器进程未关闭",
        QMessageBox.Yes
      )
    else:
      closeBot()
      event.accept()
      sys.exit()

  def resizeEvent(self,event):
    '''窗口大小改变'''
    self.resizeConsole()

class Functions(QObject):
  '''QtWeb通信模块'''
  @pyqtSlot(str, result=str)
  def bdslog(self,void):
    if not logQueue.empty():
      return logQueue.get()
    else:
      return "None"

  @pyqtSlot(str, result=str)
  def botlog(self,void):
    if not botQueue.empty():
      return botQueue.get()
    else:
      return "None"

def closeBot():
  '''关闭bot'''
  global botProcess
  try:
    psutil.Process(botProcess.pid).children()[0].kill()
  except:
    pass
  try:
    botProcess.kill()
  except:
    pass

def componentInformation():
  '''组件信息处理'''
  global MainWindow,forms,datas,sendPort,listenPort,settings
  UiFinished=False
  while True:
    time.sleep(1)
    while UiFinished:
      time.sleep(0.5)
      try:
        if not MainWindow.isVisible():
          sys.exit()
      except:
        sys.exit()
      regularList={
        "disabled":[],
        "private_admin":[],
        "private":[],
        "group_admin":[],
        "group":[]
      }
      rows=forms["regularlist"].rowCount()
      if rows>0:
        for singleRow in range(rows):
          if forms["regularlist"].item(singleRow,1):
            regular=forms["regularlist"].item(singleRow,1).text()
          else:
            regular=""
          if forms["regularlist"].item(singleRow,2):
            remark=forms["regularlist"].item(singleRow,2).text()
          else:
            remark=""
          if forms["regularlist"].item(singleRow,3):
            command=forms["regularlist"].item(singleRow,3).text()
          else:
            command=""
          captureArea=forms["regularlist"].cellWidget(singleRow,0).currentIndex()
          if captureArea==0:
            captureArea="disabled"
          elif captureArea==1:
            captureArea="private_admin"
          elif captureArea==2:
            captureArea="private"
          elif captureArea==3:
            captureArea="group_admin"
          elif captureArea==4:
            captureArea="group"
          elif captureArea==5:
            captureArea="console"
          regularList[captureArea].append({
              "regular":regular,
              "command":command,
              "remark":remark
            })
      taskList={}
      taskNameList=[]
      rows=forms["timedTask"]["timedTaskList"].rowCount()
      if rows>0:
        for singleRow in range(rows):
          if forms["timedTask"]["timedTaskList"].cellWidget(singleRow,1):
            type=forms["timedTask"]["timedTaskList"].cellWidget(singleRow,1).currentIndex()
          else:
            continue
          if forms["timedTask"]["timedTaskList"].item(singleRow,2):
            value=forms["timedTask"]["timedTaskList"].item(singleRow,2).text()
          else:
            value=""
          if forms["timedTask"]["timedTaskList"].item(singleRow,0):
            name=forms["timedTask"]["timedTaskList"].item(singleRow,0).text()
          else:
            name=""
          if forms["timedTask"]["timedTaskList"].item(singleRow,3):
            remark=forms["timedTask"]["timedTaskList"].item(singleRow,3).text()
          else:
            remark=""
          if forms["timedTask"]["timedTaskList"].item(singleRow,4):
            command=forms["timedTask"]["timedTaskList"].item(singleRow,4).text()
          else:
            command=""
          if name in taskNameList or name=="":
            continue
          else:
            taskNameList.append(name)
          taskList[name]={
              "value":value,
              "command":command,
              "name":name,
              "type":type,
              "remark":remark
            }
      datas={
        "regular":regularList,
        "taskList": taskList,
        "type":"datas"
      }
      with open(os.path.join(selfPath,"datas.json"), 'w',encoding='utf-8')as jsonFile:
        jsonFile.write(json.dumps(datas,sort_keys=True,ensure_ascii=False,indent=2))
      groupList=[]
      permissionList=[]
      if stopSavingSetting:
        continue
      for text in forms["setting"]["msg"]["groupList"].toPlainText().split("\n"):
        if  re.search('^[\d]{6,16}$',text) and text!="":
          groupList.append(int(text))
      for text in forms["setting"]["msg"]["permissionList"].toPlainText().split("\n"):
        if  re.search('^[\d]{5,13}$',text) and text!="":
          permissionList.append(int(text))
      settings={
        "type":"settings",
        "start":{
          "filepath":forms["setting"]["start"]["filepath"].text(),
          "autoRestart":forms["setting"]["start"]["autoRestart"].isChecked()
        },
        "bot":{
          "sendPort":sendPort,
          "listenPort":listenPort,
          "botFilepath":forms["setting"]["bot"]["botFilepath"].text(),
          "enableOutputMsgToLog":forms["setting"]["bot"]["enableOutputMsgToLog"].isChecked()
        },
        "console":{
          "colorfulLogOut":forms["setting"]["console"]["colorfulLogOut"].currentIndex(),
          "enableOutputToLog":forms["setting"]["console"]["enableOutputToLog"].isChecked(),
          "outputCommandToConsole":forms["setting"]["console"]["outputCommandToConsole"].isChecked()
        },
        "msg":{
          "groupList":groupList,
          "permissionList":permissionList,
          "givePermissionToAllAdmin":forms["setting"]["msg"]["givePermissionToAllAdmin"].isChecked()
        },
        "Dylan":{
          "enableUpdate":forms["setting"]["Dylan"]["enableUpdate"].isChecked(),
          "enableAnnouncement":forms["setting"]["Dylan"]["enableAnnouncement"].currentIndex(),
          "chosenTheme":forms["setting"]["Dylan"]["chosenTheme"].currentIndex()
        }
      }
      with open(os.path.join(selfPath,"setting.json"), 'w',encoding='utf-8')as jsonFile:
        jsonFile.write(json.dumps(settings,sort_keys=True,ensure_ascii=False,indent=2))
      regQueue.put(settings)
      regQueue.put(datas)
      task.updateSettings(settings)
      task.updateTaskList(taskList)
      server.updateSettings(settings)
    try:
      if MainWindow.isVisible():
        UiFinished=True
    except:
      continue

def updateWidgets():
  '''更新组件信息'''
  while True:
    time.sleep(0.5)
    if forms=={}:
      continue
    forms["timedTask"]["timedTask_state"].setText("误差时间："+task.deviation()+"s")
    if server.isRunning():
      forms["panel"]["restart"].setDisabled(False)
      forms["panel"]["forcestop"].setDisabled(False)
      forms["panel"]["input"].setDisabled(False)
      forms["panel"]["start"].setDisabled(True)
      forms["panel"]["restart"].setDisabled(False)
      forms["panel"]["stop"].setDisabled(False)
      forms["setting"]["start"]["selectfile"].setDisabled(True)
      forms["setting"]["start"]["filepath"].setDisabled(True)
      forms["panel"]["cpu"].setText(str(psutil.cpu_percent())+"%")
      forms["panel"]["ram"].setText(str(psutil.virtual_memory()[2])+"%")
    elif not server.isWaitingRestart():
      forms["panel"]["port"].setText("- / -")
      forms["panel"]["levelname"].setText("-")
      forms["panel"]["difficulty"].setText("-")
      forms["panel"]["gamemode"].setText("-")
      forms["panel"]["state"].setText("未启动")
      forms["panel"]["version"].setText("-")
      forms["panel"]["input"].setText("")
      forms["panel"]["restart"].setDisabled(True)
      forms["panel"]["forcestop"].setDisabled(True)
      forms["panel"]["input"].setDisabled(True)
      forms["panel"]["start"].setDisabled(False)
      forms["panel"]["restart"].setDisabled(True)
      forms["panel"]["stop"].setDisabled(True)
      forms["setting"]["start"]["selectfile"].setDisabled(False)
      forms["setting"]["start"]["filepath"].setDisabled(False)
      forms["panel"]["cpu"].setText("-%")
      forms["panel"]["ram"].setText("-%")
    else:
      forms["panel"]["port"].setText("- / -")
      forms["panel"]["levelname"].setText("-")
      forms["panel"]["difficulty"].setText("-")
      forms["panel"]["gamemode"].setText("-")
      forms["panel"]["state"].setText("未启动")
      forms["panel"]["version"].setText("-")
      forms["panel"]["input"].setText("")
      forms["panel"]["restart"].setDisabled(True)
      forms["panel"]["forcestop"].setDisabled(True)
      forms["panel"]["input"].setDisabled(True)
      forms["panel"]["cpu"].setText("-%")
      forms["panel"]["ram"].setText("-%")
    if server.isRunning() and server.info()!={}:
      try:
        forms["panel"]["version"].setText(server.info()["version"][:10])
        forms["panel"]["gamemode"].setText(server.info()["gamemode"])
        forms["panel"]["difficulty"].setText(server.info()["difficulty"])
        forms["panel"]["state"].setText("已启动")
        forms["panel"]["levelname"].setText(server.info()["levelname"][:20])
        forms["panel"]["port"].setText(server.info()["port"])
      except:
        pass
    if botState==1:
      if qq!=0:
        forms["bot"]["qq"].setText(str(qq))
        forms["bot"]["send"].setText(str(MessageSent))
        forms["bot"]["receive"].setText(str(MessageReceived))

def startBot():
  '''机器人启动程序'''
  global botState,botProcess,forms,settings
  while True:
    time.sleep(1)
    if forms=={}:
      continue
    if botState==1:
      with open(os.path.join(selfPath,"go-cqhttp.bat"), 'w',encoding='utf-8')as bat:
        bat.write("chcp 65001\ncd \""+os.path.split(settings["bot"]["botFilepath"])[0]+"\"\necho.#cls\n\""+settings["bot"]["botFilepath"]+"\"")
      botProcess=subprocess.Popen(
      os.path.join(selfPath,"go-cqhttp.bat"),
      stdout=subprocess.PIPE,
      stdin=subprocess.PIPE,
      universal_newlines=True,
      bufsize=1,
      encoding="UTF-8"
      )
      while botState==1:
        try:
          log=botProcess.stdout.readline()
        except:
          botState=0
        if re.search('qrcode.png',log):
          qrpath=os.path.join(os.path.split(settings["bot"]["botFilepath"])[0],"qrcode.png")
          if os.path.exists(qrpath):
            os.system(qrpath)
        if not re.search('^[\n\s\r]$',log) and log!="":
          log=outputRecognition(log)
          log=escapeLog(log)
          log=colorLog(log,2)
          botQueue.put("<span class='noColor'>"+log+"</span>")
          if log.find("请输入你需要的编号")>=0 :
            time.sleep(1)
            botProcess.stdin.write("0\n")
            botQueue.put(("[<span style='color:#007ACC'>Dylan</span>]已自动输入"))
          elif log.find("默认配置文件已生成")>=0:
            botProcess.stdin.write("\n")
          elif log.find("登录成功")>0 :
            forms["bot"]["state"].setText("运行中")
        try:
          psutil.Process(botProcess.pid)
        except:
          botState=0
    else:
      try:
        forms["bot"]["start"].setDisabled(False)
        forms["bot"]["stop"].setDisabled(True)
      except:
        break

httpServer = Flask(__name__)

@httpServer.route('/', methods=["POST"])
def post_data():
  '''数据包接收处理'''
  global settings
  if request.get_json().get("meta_event_type") == 'heartbeat':
    global qq,MessageReceived,MessageSent
    qq=request.get_json().get("self_id")
    MessageReceived=request.get_json().get("status").get("stat").get("MessageReceived")
    MessageSent=request.get_json().get("status").get("stat").get("MessageSent")
    return 'ok'
  elif request.get_json().get('message_type') == 'private' or request.get_json().get('message_type') == 'group':
    regQueue.put(request.get_json())
    if settings["bot"]["enableOutputMsgToLog"]:
      with open(os.path.join(selfPath,"log",f"msg-{datetime.date.today()}.tasksv"),"a") as tasksv:
        writeList=[
          time.time(),
          datetime.datetime.now().time(),
          request.get_json().get('message_type'),
          request.get_json().get('sender').get('nickname'),
          request.get_json().get('user_id'),
          request.get_json().get('group_id'),
          request.get_json().get('sub_type'),
          request.get_json().get('raw_message'),
          request.get_json()
        ]
        text=""
        for i in writeList:
          i=str(i).replace('"','""')
          if i==None or i == "None":
            i=""
          elif text=="":
            text=i
          else:
            text=f'{text},"{i}"'
        tasksv.write(text+"\n")
    return 'ok'

def runHttp():
  '''运行http服务器'''
  if settings.get("bot") is None:
    port=8000
  elif settings.get("bot").get("listenPort") is None:
    port=8000
  else:
    port=settings["bot"]["listenPort"]
  httpServer.run(host='127.0.0.1', port=port)

def mainGui():
  '''主窗口'''
  global MainWindow
  app.processEvents()
  app.setWindowIcon(QIcon(icoPath))
  MainWindow=gui()
  MainWindow.show()
  splashWindow.finish(MainWindow)
  splashWindow.deleteLater()
  sys.exit(app.exec_())

if __name__=="__main__":
  selfPath=os.path.dirname(os.path.realpath(sys.argv[0]))
  if not os.path.exists(os.path.join(selfPath,"datas.json")):
    datas={}
    regularList={}
    taskList=[]
  else:
    with open(os.path.join(selfPath,"datas.json"), 'r',encoding='utf-8') as jsonFile:
      try:
        datas=json.load(jsonFile)
        try:
          taskList=datas["timedTaskList"]
        except:
          taskList=[]
        try:
          regularList=datas["regular"]
        except:
          regularList={}
      except:
        datas={}
        regularList={}
        taskList=[]
  if not os.path.exists(os.path.join(selfPath,"setting.json")):
    settings={}
  else:
    with open(os.path.join(selfPath,"setting.json"), 'r',encoding='utf-8')as jsonFile:
      try:
        settings=json.load(jsonFile)
      except:
        settings={}
  QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
  app=QtWidgets.QApplication(sys.argv)
  splashWindow=splash()
  splashWindow.setAttribute(Qt.WA_TranslucentBackground)
  splashWindow.setPixmap(QPixmap('attachment/ico.png'))
  splashWindow.show()
  app.processEvents()
  channel = QWebChannel()
  Function = Functions()
  VERSION="Alpha 2.1.20220322"
  stopSavingSetting=False
  consolePath=os.path.join(selfPath,"attachment","console.html")
  icoPath=os.path.join(selfPath,"attachment","ico.png")
  logQueue=queue.Queue(maxsize=0)
  botQueue=queue.Queue(maxsize=0)
  regQueue=queue.Queue(maxsize=0)
  commandQueue=queue.Queue(maxsize=0)
  task=Task(commandQueue)
  server=Server(commandQueue,logQueue,regQueue,selfPath)
  permissionList=[]
  qq=0
  botState=0
  forms={}
  if not os.path.exists(consolePath):
    print("console.html文件不存在")
    sys.exit()
  if not os.path.exists(os.path.join(selfPath,"log")):
    os.makedirs(os.path.join(selfPath,"log"))
  getComponentInformation=threading.Thread(target=componentInformation,daemon=True)
  getComponentInformation.start()
  updating=threading.Thread(target=updateWidgets,daemon=True)
  updating.start()
  botHttpThread=threading.Thread(target=runHttp,daemon=True)
  botHttpThread.start()
  botThread=threading.Thread(target=startBot,daemon=True)
  botThread.start()
  msgThread=threading.Thread(target=lambda:regProcessing(regQueue,commandQueue),daemon=True)
  msgThread.start()
  mainGui()
