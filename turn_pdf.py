import sys

from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
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
turnCurr = 0

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
   turnButton.clicked.connect(lambda: turnButton_clicked(settings["printer_name"], widget))

   widget.setGeometry(0, 0, screenW, screenH)
   widget.setWindowTitle(settings["window_label_text"])
   widget.showMaximized()
   
   widget.setWindowFlags(Qt.WindowStaysOnTopHint)
   widget.setWindowFlag(Qt.WindowCloseButtonHint, False)
   widget.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
   widget.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
   
   widget.show()
   sys.exit(app.exec_())

def turnButton_clicked(printerName, widget):
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

   #Calculating current turn
   global turnCurr
   turnCurr += 1

   if turnCurr > 99:
      turnCurr = 1
   if turnCurr > 9:
      turnStr = str(turnCurr)
   else:
      turnStr = "0" + str(turnCurr)

   #Creating plain text
   tmpSource = tempfile.mktemp (".txt")
   open (tmpSource, "a").write ("Turn: \n")
   if turnCurr > 9:
     open (tmpSource, "a").write (str(turnCurr))
   else:
     open (tmpSource, "a").write ("0"+str(turnCurr))
   open (tmpSource, "a").write ("\n"+nowStr)
   open (tmpSource, "a").write("\nNAME") #TODO set from settings.json

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

   story = []
   story.append(Paragraph(text[0], myNormal))
   story.append(Paragraph(text[1], myH1))
   story.append(Paragraph(text[2], myNormal))
   story.append(Paragraph(text[3], myItalic))
   story.append(Paragraph("\n ", myNormal))
   
   doc.build(story)
   
   #Printing (printer taken from settings.json)
   win32api.ShellExecute(0, "printto", tmpFile, f'"{printerName}"', ".", 0)



if __name__ == '__main__':
   window()

