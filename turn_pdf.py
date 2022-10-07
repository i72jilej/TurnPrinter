import sys

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import pyqtSlot, QSize, Qt

from datetime import datetime

import tempfile
import win32api
import win32print

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import html

import json

#Global var for counting turns
turnCurr = 1

#Styles for the text lines
styles = getSampleStyleSheet()
myNormal = ParagraphStyle('myNormal',
                           fontSize=20,
                           parent=styles["Normal"],
                           spaceAfter=14)
myH1 = ParagraphStyle('myH1',
                          fontSize=30,
                          parent=styles["h1"],
                          spaceAfter=14)
myItalic = ParagraphStyle('myItalic',
                           fontSize=18,
                           parent=styles["Italic"],
                           spaceAfter=14)

#Class for the waiting message box
class CustomMessageBox(QMessageBox):
   def __init__(self, *__args):
      QMessageBox.__init__(self)
      self.timeout = 0
      self.autoclose = False
      self.currentTime = 0
      self.setWindowFlags(Qt.WindowStaysOnTopHint)
      self.setWindowFlag(Qt.WindowCloseButtonHint, False)
      self.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
      self.setWindowFlag(Qt.WindowMaximizeButtonHint, False)

   def showEvent(self, QShowEvent):
      self.currentTime = 0
      if self.autoclose:
         self.startTimer(1000)

   def timerEvent(self, *args, **kwargs):
      self.currentTime += 1
      if self.currentTime >= self.timeout:
         self.done(0)

   @staticmethod
   def showWithTimeout(timeoutSeconds, message, title, icon=QMessageBox.Information):
      w = CustomMessageBox()
      w.autoclose = True
      w.timeout = timeoutSeconds
      w.setText(message)
      w.setWindowTitle(title)
      w.setIcon(icon)
      w.exec_()

#Main Program
def window():
   app = QApplication(sys.argv)
   widget = QWidget()

   #Taking screen size
   screenH = app.primaryScreen().size().height()
   screenW = app.primaryScreen().size().width()

   #Reading settings.json
   with open('settings.json', 'r') as f:
      settings = json.load(f)

   #Creating button and giving it style
   turnButton = QPushButton(widget)
   turnButton.setText(settings["button_label_text"])
   turnButton.setFont(QFont("Calibri", settings["button_text_size"]))
   turnButton.setGeometry(int(screenW - (screenW * 0.79)),
                           int(screenH - (screenH * 0.79)), 
                           int(screenW - (screenW * 0.42)),
                           int(screenH - (screenH * 0.47)))
   buttonStyleString = "border-radius: " + str(settings["button_border_radius"]) + "; " + "border: " + settings["button_border_width"] + " " + settings["button_border_style"] + " " + settings["button_border_color"] +"; " + "background: " + settings["button_background_color"] + "; " + "color: " + settings["button_label_color"]

   #turnButton.setStyleSheet("border-radius: 250; border: 2px solid black; background: #3001c9; color: #7fdd00")
   turnButton.setStyleSheet(buttonStyleString)
   turnButton.setIcon(QIcon(settings["button_icon_filename"]))
   turnButton.setIconSize(QSize(settings["button_icon_size_W"],settings["button_icon_size_H"]))
   turnButton.clicked.connect(lambda: turnButton_clicked(settings["printer_name"], settings["ticket_turn_label"], settings["ticket_store_name"], settings["debug_mode"] ,widget))

   widget.setGeometry(0, 0, screenW, screenH)
   widget.setWindowTitle(settings["window_title_text"])
   widget.showMaximized()
   
   widget.setWindowFlags(Qt.WindowStaysOnTopHint)
   widget.setWindowFlag(Qt.WindowCloseButtonHint, False)
   widget.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
   widget.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
   
   widget.show()
   sys.exit(app.exec_())

def turnButton_clicked(printerName, turnLabel, storeName, debugMode, widget):
   #Getting current turn number
   global turnCurr

   #Building the date line
   now = datetime.now()
   if now.day < 9:
      nowStr = "0" + str(now.day) + "/"
   else:
      nowStr = str(now.day) + "/"

   if now.month < 9:
      nowStr += "0" + str(now.month) + "/"
   else:
      nowStr += str(now.month) + "/"

   nowStr += str(now.year) + "  "

   if now.hour < 9:
      nowStr += "0" + str(now.hour) + ":"
   else:
      nowStr += str(now.hour) + ":"

   if now.minute < 9:
      nowStr += "0" + str(now.minute) + ":"
   else:
      nowStr += str(now.minute) + ":"

   if now.second < 9:
      nowStr += "0" + str(now.second)
   else:
      nowStr += str(now.second)

   #Creating plain text
   tmpSource = tempfile.mktemp (".txt")
   open (tmpSource, "a").write (turnLabel+"\n")
   if turnCurr > 9:
     open (tmpSource, "a").write (str(turnCurr))
   else:
     open (tmpSource, "a").write ("0"+str(turnCurr))
   open (tmpSource, "a").write ("\n"+nowStr)
   open (tmpSource, "a").write("\n"+storeName) #TODO set from settings.json

   #Creating PDF file for printing
   tmpFile = tempfile.mktemp(".pdf")
   pagesize = (72.07 * mm, 209.96 * mm)
   doc = SimpleDocTemplate(tmpFile, 
                           pagesize = pagesize, 
                           leftMargin = 0.0 * mm, 
                           rightMargin = 0.0 * mm, 
                           topMargin = 0.0 * mm, 
                           bottomMargin = 5.0 * mm)
   text = html.escape(open(tmpSource).read()).splitlines()

   #Giving style to the different lines
   global myNormal
   global myH1
   global myItalic

   if debugMode == 1:
      print(text)

   story = []
   story.append(Paragraph(text[0], myNormal))
   story.append(Paragraph(text[1], myH1))
   story.append(Paragraph(text[2], myNormal))
   story.append(Paragraph(text[3], myItalic))
   story.append(Paragraph("\n ", myNormal))
   
   doc.build(story)
   
   #Printing (printer taken from settings.json)
   if debugMode == 0:
      win32api.ShellExecute(0, "printto", tmpFile, f'"{printerName}"', ".", 0)
   else:
      print("WARNIGN: Debug mode activated, ticket not printed")

   #Showing wait message box
   msg = CustomMessageBox.showWithTimeout(3, "Auto close in 3 seconds", "QMessageBox with autoclose", icon=QMessageBox.Warning)

   #Calculating next turn
   turnCurr += 1
   if turnCurr > 99:
      turnCurr = 1
   if turnCurr > 9:
      turnStr = str(turnCurr)
   else:
      turnStr = "0" + str(turnCurr)


if __name__ == '__main__':
   window()

