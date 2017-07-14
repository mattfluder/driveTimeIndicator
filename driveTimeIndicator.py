#!/usr/bin/env python
import signal
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk, AppIndicator3, GObject
import time
import googlemaps
import webbrowser
import urllib
import csv
import os
import traceback
from datetime import datetime, date
from threading import Thread

class Indicator():
    def __init__(self):
        self.app = 'gmapTimeIndicator1'
        iconpath = "./car-32.ico"
        self.indicator = AppIndicator3.Indicator.new(
            self.app, iconpath,
            AppIndicator3.IndicatorCategory.OTHER)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())
        self.indicator.set_label("N/A", self.app)
        self.preferenceWindow = PreferenceWindow(self)
        # the thread:
        self.update = Thread(target=self.updateTimeLoop)
        # daemonize the thread to make the indicator stopable
        self.update.setDaemon(True)
        self.update.start()

    def create_menu(self):
        menu = Gtk.Menu()
        # Open in browser
        item_browser = Gtk.MenuItem('Open In Browser')
        item_browser.connect('activate', self.openInBrowser)
        menu.append(item_browser)
        item_browser = Gtk.MenuItem('Preferences')
        item_browser.connect('activate', self.setLocationGUI)
        menu.append(item_browser)
        # separator
        menu_sep = Gtk.SeparatorMenuItem()
        menu.append(menu_sep)
        # quit
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def updateTravelTime(self):
        try:
            self.gmaps = googlemaps.Client(key=self.preferenceWindow.apiKey)
            nowTime=datetime.now()
            directions_result= self.gmaps.directions(self.preferenceWindow.startLocation, self.preferenceWindow.endLocation,avoid="tolls", departure_time=nowTime)
            duration = directions_result[0]["legs"][0]["duration_in_traffic"]["text"]
            summary = directions_result[0]['summary']
            mention = duration + ' ' + summary
            durationValue = directions_result[0]["legs"][0]["duration_in_traffic"]["value"]
            durationMinutes = durationValue/60.0
            row= [nowTime.__format__("%y-%m-%d  %H:%M"),durationMinutes, directions_result[0]["legs"][0]["duration_in_traffic"]["value"], summary, self.preferenceWindow.startLocation, self.preferenceWindow.endLocation]
            fileLocation = self.preferenceWindow.dataFileLocation + "time_data_" + date.today().strftime('%Y-%m-%d') + ".csv"
            if os.path.exists(fileLocation):
                append_write = 'a' # append if already exists
            else:
                append_write = 'w' # make a new file if not
            icsvFile = open(fileLocation, append_write)
            csvwriter = csv.writer(icsvFile, quoting=csv.QUOTE_NONNUMERIC)
            csvwriter.writerow(row)
            icsvFile.close()

        except(googlemaps.exceptions.ApiError, googlemaps.exceptions.HTTPError, googlemaps.exceptions.Timeout, googlemaps.exceptions.TransportError):
            mention ='Maps Error'
        except:
            mention ='General Error'
            traceback.print_exc()
        # apply the interface update using  GObject.idle_add()
        GObject.idle_add(
                self.indicator.set_label,
                mention, self.app,
                priority=GObject.PRIORITY_DEFAULT
                )

    def updateTimeLoop(self):
        while True:
            self.updateTravelTime()
            time.sleep(60)



    def openInBrowser(self, source):
        startURL = urllib.quote_plus(self.preferenceWindow.startLocation)
        endURL = urllib.quote_plus(self.preferenceWindow.endLocation)
        url = 'https://www.google.ca/maps/dir/' + startURL + '/' + endURL + '/'
        webbrowser.open(url, new=0, autoraise=True)

    def setLocationGUI(self,source):
        self.preferenceWindow.show_all()

    def stop(self, source):
        Gtk.main_quit()

class PreferenceWindow(Gtk.Window):
    def __init__(self, indicator):
        Gtk.Window.__init__(self, title="Preferences")
        self.apiKey = ''
        self.startLocation = ""
        self.endLocation = ""
        self.dataFileLocation = "./"
        self.connect('delete-event', self.hide_window)
        self.indicator = indicator
        grid = Gtk.Grid(column_spacing=5,row_spacing=10)
        self.add(grid)
        startLabel = Gtk.Label("Start Location:")
        endLabel = Gtk.Label("End Location:")
        apiLabel = Gtk.Label("API Key:")
        fileLabel = Gtk.Label("File Location:")
        saveButton = Gtk.Button(label="Save")
        saveButton.connect("clicked", self.saveEntries)
        cancelButton = Gtk.Button(label="Cancel")
        cancelButton.connect("clicked", self.hide_window)
        self.startEntry = Gtk.Entry()
        self.startEntry.set_width_chars(50)
        self.startEntry.set_text(self.startLocation)
        self.endEntry = Gtk.Entry()
        self.endEntry.set_text(self.endLocation)
        self.keyEntry = Gtk.Entry()
        self.keyEntry.set_text(self.apiKey)
        self.fileEntry = Gtk.Entry()
        self.fileEntry.set_text(self.dataFileLocation)
        grid.attach(startLabel,0,0,1,1)
        grid.attach(self.startEntry,1,0,1,1)
        grid.attach(endLabel,0,1,1,1)
        grid.attach(self.endEntry,1,1,1,1)
        grid.attach(apiLabel,0,2,1,1)
        grid.attach(self.keyEntry,1,2,1,1)
        grid.attach(fileLabel,0,3,1,1)
        grid.attach(self.fileEntry,1,3,1,1)
        grid.attach(cancelButton, 0, 4, 1, 1)
        grid.attach(saveButton, 1, 4, 1, 1)

    def hide_window(window,event, data=None):
        window.hide()
        return True

    def saveEntries(window,event):
        window.setAPIKey(window.keyEntry.get_text())
        window.setStartLocation(window.startEntry.get_text())
        window.setEndLocation(window.endEntry.get_text())
        window.hide()
        window.indicator.updateTravelTime()
        return True

    def getStartLocation(self):
        return self.startLocation

    def setStartLocation(self, startLocation):
        self.startLocation = startLocation

    def getEndLocation(self):
        return self.endLocation

    def setEndLocation(self, endLocation):
        self.endLocation = endLocation

    def setAPIKey(self, apiKey):
        self.apiKey = apiKey

    def getAPIKey(self, apiKey):
        return self.apiKey

Indicator()
# this is where we call GObject.threads_init()
GObject.threads_init()
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
