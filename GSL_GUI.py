#! /usr/bin/env python3
from __future__ import print_function

from tkinter import *
import requests
import csv
import io


import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

import datetime
import re

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

def resource_path(relative_path):
     '''set path for pyinstaller'''
     if hasattr(sys, '_MEIPASS'):
         return os.path.join(sys._MEIPASS, relative_path)
     return os.path.join(os.path.abspath("."), relative_path)

SCOPES = 'https://www.googleapis.com/auth/spreadsheets'
CLIENT_SECRET_FILE = resource_path('client_secret.json')
APPLICATION_NAME = 'GUI-for-EC'

class SpreadsheetHandler():

    def __init__(self):
        self.service = self.login()
        #test
        #self.spreadsheetId = '1-lMc3ecLBmf8oJLWZipxapC_F1upByCd9UaA8YepZtc'
        self.spreadsheetId = '1zeuYtXUNRVeY-CUW9jUi7s_nF5VaQ9DoIvOgFzXnsuQ'
        #self.spreadsheetName = "test"
        self.spreadsheetName = "GS-Liste"



    def get_credentials(self):
        """Gets valid user credentials from storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.

        Returns:
            Credentials, the obtained credential.
        """
        home_dir = os.path.expanduser('~')
        credential_dir = os.path.join(home_dir, '.credentials')
        if not os.path.exists(credential_dir):
            os.makedirs(credential_dir)
        credential_path = os.path.join(credential_dir,
                                       'sheets.googleapis.com-python-quickstart.json')

        store = Storage(credential_path)
        credentials = store.get()
        if not credentials or credentials.invalid:
            flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
            flow.user_agent = APPLICATION_NAME
            if flags:
                credentials = tools.run_flow(flow, store, flags)
            else: # Needed only for compatibility with Python 2.6
                credentials = tools.run(flow, store)
            print('Storing credentials to ' + credential_path)
        return credentials

    def login(self):
        credentials = self.get_credentials()
        http = credentials.authorize(httplib2.Http())
        discoveryUrl = ('https://sheets.googleapis.com/$discovery/rest?'
                    'version=v4')
        service = discovery.build('sheets', 'v4', http=http,
                              discoveryServiceUrl=discoveryUrl)
        return service

    def load_data(self):

        rangeName = self.spreadsheetName+'!A1:S175'
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.spreadsheetId, range=rangeName).execute()
        values = result.get('values', [])

        rownum = 0
        header = 4
        labels = ["row"]
        raw = {}
        data = []

        for row in values:
            if rownum == header:
                for col in row:
                    raw[col] = ''
                    labels.append(col)

            elif rownum > header:
                i = 0
                for col in row:
                    raw[labels[i+1]] = col
                    raw["row"] = rownum + 1
                    i = i +1
                temp = raw.copy()
                if temp["x0"] != "":
                    data.append(temp)

            rownum = rownum + 1

        labeled = {}
        for GS in data:
            labeled[GS["ID"]] = GS

        self.data = labeled
        return labeled

    def write(self, row, col, val, vio="RAW"):
        '''writes into single cell'''

        ColumnLetters = {
            "ID":"A",
            "x0":"B",
            "x1":"C",
            "y0":"D",
            "y1":"E",
            "Besitzer":"F",
            "Mitbewohner":"G",
            "Offlinezeit":"H",
            "Verkaufsschild":"I",
            "Preis":"K",
            "Status":"R"
        }

        range = self.spreadsheetName + "!" + ColumnLetters[col] + row + ":" + ColumnLetters[col] + row
        value_input_option = vio

        values = [
            [
                val
            ]
        ]
        body = {
          'values': values
        }
        result = self.service.spreadsheets().values().update(
            spreadsheetId=self.spreadsheetId, range=range,
            valueInputOption=value_input_option, body=body).execute()

class LogHandler():

    def __init__(self, master=None, default_id="s037-"):
        self.master = master
        self.entryID_default = default_id
        self.handler = SpreadsheetHandler()
        self.data = self.handler.load_data()
        self.input_option = "RAW"
        self.changes = []

    def scan_for_info(self,lines, index):

        if "You're" in lines[index-1]:
            return None

        owner = lines[index][1]

        for i in range(0, 10):
            line = lines[index+i]

            if len(line) < 2:
                continue

            #region id
            elif line[0] == "Region:":
                id = line[1]

            #members
            elif line[0] == "Members:":
                members = str([name.replace("*","").replace(",","") for name in line[1:]])[1:-1]

            #offline duration
            elif line[1] == "ist":

                weeks = 0
                days = 0
                for j in range(0,len(line)):
                    if "Woche" in line[j]:
                        weeks = line[j-1]
                    if "Tag" in line[j]:
                        days = line[j-1]
                date = str(weeks)+"w"+str(days)+"d"


        infos = {id: {"owner": owner,
                        "members": members,
                        "offline": date}}
        return infos

    def read_log(self):

        path = os.getenv('APPDATA')+"\\.minecraft\\logs\\latest.log"
        #path = os.getenv('APPDATA')+"\\.minecraft\\logs\\testlog.log"

        f = open(path)

        #GS-Liste
        gs = {}

        lines = [line.split()[4:] for line in f.readlines()]

        for i in range(0, len(lines)):

            line = lines[i]

            try:

                if line[0] == "Regionsbesitzer:":
                    region = self.scan_for_info(lines, i)
                    if region != None:
                        gs.update(region)

            except IndexError:
                continue

        return gs

    def update_from_log(self, region, ID):

        self.ID = ID
        if ID not in self.data.keys():
            return

        for key in region.keys():

            if key == "offline":
                    self.field = "Offlinezeit"
                    self.val = region[key]
                    if 'd' in self.val:
                        def _comp_days():
                            days = re.findall(r'\dd', self.val)
                            weeks = re.findall(r"\dw", self.val)
                            if days:
                                days = int(days[0][0])
                            else:
                                days = 0
                            if weeks:
                                weeks = int(weeks[0][0])
                            else:
                                weeks = 0
                            dif = days + (weeks*7)
                            return dif

                        today = datetime.date.today()
                        newData = today - datetime.timedelta(days=_comp_days())
                        self.val = '=TO_DATE(DATEVALUE("'+str(newData)+'"))'
                        self.input_option = "USER_ENTERED"

            elif key == "owner":
                self.field = "Besitzer"
                self.val = region[key]
                self.input_option = "RAW"

                if self.data[ID]["Besitzer"] != self.val:
                    self.changes.append([ID, self.data[ID]["Besitzer"], self.val])


            elif key == "members":
                self.field = "Mitbewohner"
                self.val = region[key]
                self.input_option = "RAW"

            else:
                continue
                self.input_option = "RAW"

            if self.ID in self.data.keys():
                    self.row = self.data[self.ID]["row"]
                    self.handler.write(str(self.row), self.field, self.val, self.input_option)
                    self.data[self.ID][self.field] = self.val
            else:
                    None

class MainWindow(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.version = "v.3.0"
        self.master = master
        self.master.title("GSL GUI "+"\t" + self.version)
        self.data = self.get_data_from_drive()
        self.widgets = {}
        self.tooltip = -1
        self.menubar = self.create_menu(master)

        master.config(menu=self.menubar)
        frame = self.create_filter(master)
        frame.pack(fill=BOTH)
        self.canvas = self.create_canvas(master)
        self.canvas.pack()
        self.prev_search = -1



    def create_menu(self, master):

        menubar = Menu(master)

        helpmenu = Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Help", command=self.help)
        helpmenu.add_command(label="Check for updates...", command=self.upd)
        helpmenu.add_command(label="About...", command=self.about)
        menubar.add_cascade(label="Hilfe", menu=helpmenu)

        editmenu = Menu(menubar, tearoff=0)
        editmenu.add_command(label="Edit Drive", command=self.open_edit)
        editmenu.add_command(label="Read from Log", command=self.read_from_log)
        menubar.add_cascade(label="Bearbeiten", menu=editmenu)

        searchmenu = Menu(menubar, tearoff=0)
        searchmenu.add_command(label="Spielersuche", command=self.player_search)
        menubar.add_cascade(label="Suche", menu=searchmenu)



        return menubar



    def mock_data(self):

            data = {
                  's037-175-76':  {'y1': 130, 'date': '03.01.2017', 'prize': '125000', 'owner': 'Balthuris', 'x0': 66, 'ID': 's037-175-76', 'x1': 89, 'y0': 99},
                  's037-41':  {'y1': 536, 'date': '08.12.2016', 'prize': '400000', 'owner': '_gismo_', 'x0': 136, 'ID': 's037-41', 'x1': 174, 'y0': 469},
                  's037-cm':  {'y1': 478, 'date': '05.12.2016', 'prize': '55000', 'owner': 'ascplayer', 'x0': 180, 'ID': 's037-cm', 'x1': 196, 'y0': 455},
                  's037-65':  {'y1': 532, 'date': '06.12.2016', 'prize': '339000', 'owner': 'Angelimir', 'x0': 271, 'ID': 's037-65', 'x1': 318, 'y0': 498},
                  's037-cm92':  {'y1': 317, 'date': '15.12.2016', 'prize': '125000', 'owner': 'AnnoNuehm', 'x0': 53, 'ID': 's037-cm92', 'x1': 80, 'y0': 289},
                  's037-10':  {'y1': 229, 'date': '28.12.2016', 'prize': '41999', 'owner': 'brandikus', 'x0': 434, 'ID': 's037-10', 'x1': 453, 'y0': 242},
                  's037-14':  {'y1': 229, 'date': '03.01.2017', 'prize': '528000', 'owner': '0_0nobody0_0', 'x0': 526, 'ID': 's037-14', 'x1': 481, 'y0': 279},
                  's037-182':  {'y1': 151, 'date': '15.12.2016', 'prize': '62700', 'owner': 'Akyriel', 'x0': 93, 'ID': 's037-182', 'x1': 114, 'y0': 133},
                  's037-schloss':  {'y1': 554, 'date': '08.12.2016', 'prize': '3648000', 'owner': '_gismo_', 'x0': 130, 'ID': 's037-schloss', 'x1': 3, 'y0': 460},
                  's037-173':  {'y1': 196, 'date': '03.01.2017', 'prize': '1000000', 'owner': '0_0nobody0_0', 'x0': 2, 'ID': 's037-173', 'x1': 61, 'y0': 135}
            }

            return data

    def get_data_from_drive(self):
        headers={}
        headers["User-Agent"]= "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0"
        headers["DNT"]= "1"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Accept-Encoding"] = "deflate"
        headers["Accept-Language"]= "en-US,en;q=0.5"

        #small
        #file_id="1-lMc3ecLBmf8oJLWZipxapC_F1upByCd9UaA8YepZtc"
        #all
        file_id="1zeuYtXUNRVeY-CUW9jUi7s_nF5VaQ9DoIvOgFzXnsuQ"

        url = "https://docs.google.com/spreadsheets/d/{0}/export?format=csv".format(file_id)

        r = requests.get(url)

        data = []
        cols = []
        raw = {}

        sio = io.StringIO(r.text, newline=None)
        reader = csv.reader(sio, dialect=csv.excel)
        rownum = 0

        for row in reader:
            if rownum == 4:
                for col in row:
                    raw[col] = ''
                    cols.append(col)

            elif rownum > 4:
                i = 0
                for col in row:
                    raw[cols[i]] = col
                    i = i +1
                temp = raw.copy()
                if temp["x0"] != "":
                    data.append(temp)
            else:
                None
            rownum = rownum + 1

        x = 613 + 2
        y = 3745 + 2
        formated = {}

        for GS in data:

            GS["x0"] = int(GS["x0"]) + x
            GS["x1"] = int(GS["x1"]) + x
            GS["y0"] = int(GS["y0"]) + y
            GS["y1"] = int(GS["y1"]) + y
            formated[GS["ID"]] = GS

        return formated

    def display_info(self, id, hide=False):

            if hide:
                self.tooltip.destroy()

            else:
                self.tooltip = Toplevel()
                self.tooltip.wm_overrideredirect(True)

                text = self.data[id]["ID"]+"\n" + self.data[id]["Besitzer"] + "\n" + self.data[id]["Preis"] + "\n" + self.data[id]["len"] + "x" + self.data[id]["wid"]
                if len(self.data[id]["Besitzer"]) > len(self.data[id]["ID"]):
                    wid = len(self.data[id]["Besitzer"])
                else:
                    wid = len(self.data[id]["ID"])

                self.tooltip.minsize(width=wid*7, height=55)
                self.tooltip.maxsize(width=wid*7, height=55)

                label = Label(self.tooltip, text=text, justify=CENTER, background='yellow', relief='solid', borderwidth=1, font=("times", "8", "normal"))

                x = root.winfo_pointerx()
                y = root.winfo_pointery()
                height = 20
                geom = "+%d+%d" % (x, y+height)
                self.tooltip.geometry(geom)
                label.pack(fill=BOTH)

    def open_Dialog(self, id):
        root = Tk()
        mw = ManagerWindow(root, id)
        mw.show_details()
        r = Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(r'/rg i '+id)
        r.destroy()

    def draw_rect(self, master, id, singleSearch=False, multiSearch=False, showAll=False, demolish=False, oust=False):

        if singleSearch:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="orange", tags=id)

        elif multiSearch:
            if showAll:
                master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="pink", tags=id)
            else:
                master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="green", tags=id)
        elif demolish:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="red", tags=id)
        elif oust:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="red", tags=id)
        else:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], tags=id, fill="white", stipple="gray12")

    def create_canvas(self, master):

            self.canv = Canvas(master, width=604, height=604, relief=SUNKEN)
            img = resource_path("bg_GUI.png")
            self.map = PhotoImage(file=img)
            self.canv.create_image(304, 295, image=self.map)
            for id in self.data.keys():

                def tooltip(x, hide):
                    return lambda ev: self.display_info(x, hide)

                def onClick(id):
                    return lambda ev: self.open_Dialog(id)

                self.widgets[id] = self.draw_rect(self.canv, id)
                self.canv.tag_bind(id, '<Enter>', tooltip(id, False))
                self.canv.tag_bind(id, '<Leave>', tooltip(id, True))

                self.canv.tag_bind(id, '<ButtonPress-1>', onClick(id))

            return self.canv

    def create_filter(self, master):
        frame = Frame(master, bd=1, pady=5, padx=2,  relief=RIDGE)

        #column 0
        label_suche = Label(frame, text="Einzelsuche").grid(row=0, column=0, padx=5, sticky=SW)
        self.entry_suche = Entry(frame)
        self.entry_suche.grid(row=1, column=0, padx=5)
        bottom_frame = Frame(frame,relief='solid').grid(row=3, column=0, columnspan=5, padx=5)
        self.button_refresh = Button(frame, text="refresh", width=15)
        self.button_refresh.grid(row=2, column=0, padx=5)

        #column 1
        label_filter = Label(frame, text="Filter").grid(row=0, column=1, padx=5, sticky=E)
        #sep_frame = Frame(frame, width=50, bg="black").grid(row=1, column=1, rowspan=2)

        #column 2

        label_spanne = Label(frame, text="Preisspanne").grid(row=1, column=2, padx=5)
        self.var_bebaut = BooleanVar()
        self.check_bebaut = Checkbutton(frame, text="bebaut", variable=self.var_bebaut, onvalue=True)
        self.check_bebaut.grid(row=2, column=2, padx=5, sticky=W)
        self.var_unbebaut = BooleanVar()
        self.check_unbebaut = Checkbutton(frame, text="unbebaut", variable=self.var_unbebaut, onvalue=True)
        self.check_unbebaut.grid(row=3, column=2, padx=5, sticky=W)

        #column 3

        self.entry_min = Entry(frame, width=10)
        self.entry_min.grid(row=1, column=3, padx=5, sticky=E)

        #column 4
        label_bis = Label(frame, text="bis").grid(row=1, column=4, padx=2)
        self.var_abriss = BooleanVar()
        self.check_abriss = Checkbutton(frame, text="zum Abriss", variable=self.var_abriss, onvalue=True)
        self.check_abriss.grid(row=2, column=4, padx=5, sticky=W)
        self.var_oust = BooleanVar()
        self.check_oust = Checkbutton(frame, text="zur Enteignung", variable=self.var_oust, onvalue=True)
        self.check_oust.grid(row=3, column=4, padx=5, sticky=W)

        #column 5
        self.entry_max = Entry(frame, width=10)
        self.entry_max.grid(row=1, column=5, padx=5, sticky=W)

        #column 6
        self.button_search = Button(frame, text="suchen", width=15)
        self.button_search.grid(row=3, column=6, columnspan=2, padx=2, sticky=NW)


        #functionality
        self.entry_suche.bind('<Return>', self.single_search)
        self.entry_suche.insert(10, "s037-")

        self.button_search.bind('<ButtonPress-1>', self.search_all)
        self.button_refresh.bind('<ButtonPress-1>', self.refresh)

        return frame

    def single_search(self, event):

            self.redraw_canvas()
            request = self.entry_suche.get()

            if request in self.data.keys():
                self.draw_rect(self.canv, request, True)
            else:
                None

    def search_all(self, event):

        self.minPrize = self.entry_min.get()
        self.maxPrize = self.entry_max.get()
        self.redraw_canvas()

        def _ids_in_range(ids):
            inRange = []
            for id in ids:
                prize = self.data[id]["Preis"]
                if prize == '':
                    continue
                else:
                    prize = int(prize)
                if (prize >= self.minPrize) and (prize <= self.maxPrize):
                    inRange.append(id)
            return inRange

        def _has_building(ids, empty=False):
            build_up = []
            for id in ids:
                building = self.data[id]["Status"]
                if building == "b" and not empty:
                    build_up.append(id)
                elif building == "l" and empty:
                    build_up.append(id)
            return build_up

        sellable = []
        ownedByCity = []

        for gs in self.data.keys():
            if (self.data[gs]["Besitzer"] == "Q + S"):
                if self.data[gs]["Verkaufsschild"] == "y":
                    sellable.append(gs)
                else:
                    ownedByCity.append(gs)

        if self.minPrize == "":
            self.minPrize = 40000
        else:
            self.minPrize = int(self.minPrize)
        if self.maxPrize == "":
            self.maxPrize = 1000000
        else:
            self.maxPrize = int(self.maxPrize)

        #filter for range
        sellable = _ids_in_range(sellable)
        ownedByCity = _ids_in_range(ownedByCity)

        b = self.var_bebaut.get()
        l = self.var_unbebaut.get()
        if l and not b:
            unbebaut = _has_building(sellable, True)
            sellable = unbebaut
            unbebaut = _has_building(ownedByCity, True)
            ownedByCity = unbebaut
        elif b and not l:
            bebaut = _has_building(sellable)
            sellable = bebaut
            bebaut = _has_building(ownedByCity)
            ownedByCity = bebaut
        elif b and l:
            bebaut = _has_building(sellable)
            unbebaut = _has_building(sellable, True)
            sellable = unbebaut + bebaut
            bebaut = _has_building(ownedByCity)
            unbebaut = _has_building(ownedByCity, True)
            ownedByCity = unbebaut + bebaut

        #zum Abriss
        if self.var_abriss.get():
            sellable = []
            ownedByCity = []
            self.canv.destroy()
            self.canvas = self.create_canvas(self.master)
            self.canvas.pack()
            for gs in self.data.keys():
                if self.data[gs]["Status"].lower() == "x":
                    self.draw_rect(self.canv, gs, False, False, False, True)

        #zur Enteignung
        if self.var_oust.get():
            sellable = []
            ownedByCity = []
            self.canv.destroy()
            self.canvas = self.create_canvas(self.master)
            self.canvas.pack()
            for gs in self.data.keys():
                if self.data[gs]["Besitzer"] != "Q + S":
                    dif = datetime.date.today() - datetime.datetime.strptime(self.data[gs]["Offlinezeit"], "%d.%m.%Y").date()
                    if dif.days >= 30:
                        self.draw_rect(self.canv, gs, False, False, False, False, True)

        #draw
        for gs in sellable:
            self.draw_rect(self.canv, gs, False, True)

        for gs in ownedByCity:
            self.draw_rect(self.canv, gs, False, True, True)

    def redraw_canvas(self):
        self.canv.destroy()
        self.canvas = self.create_canvas(self.master)
        self.canvas.pack()

    def refresh(self, event):
        self.data = self.get_data_from_drive()
        self.redraw_canvas()

    def help(self):
        root = Toplevel()
        text = "Read the fucking manual!" +"\n"+ "\n"+ \
            "Der Spawn ist der Platz ohne GS Markierungen links unter dem Mittelpunkt der Karte!" + "\n" \
            "Die GS-Einzelsuche wird durch enter aktiviert und hat nichts mit dem suchen-Button (rechte Seite) zu tun." + "\n" \
            "Einzelsuchergebnisse ueberschreiben vorher markierte Felder, sodass es danach zu Farbverlusten von Felder kommen kann." + "\n" \
            "Bei einer Suche nach zum Abriss stehenden GS werden alle anderen Auswahlparameter (Preisspanne, etc.) ignoriert." + "\n" \
            "Wird ein Feld in der Preisspanne freigelassen, so wird der entsprechende Wert automatisch als 40k (bei Minimum) oder 1kk (bei Maximum) gesetzt."
        label = Label(root, text=text)
        label.pack()

    def about(self):
        root = Toplevel()
        text = "GSL GUI "+ self.version + "\n" + \
               "GSL GUI wird entwickelt und gestaltet von einer globalen Community, die daran arbeitet, dass EC einfacher wird." + "\n" + "\n"+ \
               "GSL GUI ist eine freie Software. GSL GUI wird Ihnen unter den Bedingungen der Carvahallian Public License zur Verfuegung gestellt." +"\n" \
               "Das bedeutet, dass Sie sich im Laufe ihrer EC Laufbahn zu einem GS Kauf in besagter Stadt verpflichten." + "\n"+ "\n" \
               "Wollen Sie uns unterstuetzen? Spenden Sie! An mich... alles!" + "\n"+ "\n" \
               "Unter welchen Umstaenden geben wir Ihre Daten an Dritte weiter?" + "\n" \
               " - Immer und ungefragt!"
        label = Label(root, text=text)
        label.pack()

    def upd(self):
        root = Toplevel()
        label = Label(root, text="Computer says no")
        label.pack()

    def open_edit(self):
        root = Tk()
        ManagerWindow(root)

    def read_from_log(self):

        lr = LogHandler()
        updatedGS = lr.read_log()
        #print(updatedGS)
        #print(type(updatedGS))
        for region in updatedGS.keys():
            #print("MAINFRAME")
            lr.update_from_log(updatedGS[region], region)
        print("Updating complete!")

        root = Toplevel()
        root.title("Owner Changes")
        root.minsize(width=500, height=200)
        text = ""
        for change in lr.changes:
            ID, old, new = change
            text += ID + " "+ " || " +old + " -> " + " || " +new + "\n"
        if lr.changes == []:
            text = "Keine Aenderungen"
        label = Label(root, text=text)
        label.pack()

    def player_search(self):
        root = Tk()
        SearchWindow(root)


class ManagerWindow(Frame):

    def __init__(self, master=None, default_id="s037-"):
        Frame.__init__(self, master)
        self.master = master
        self.access = False
        self.master.title("Bearbeiten")
        self.entryID_default = default_id
        self.handler = SpreadsheetHandler()
        self.data = self.handler.load_data()
        interface = self.create_interface(master)
        self.input_option = "RAW"



    def create_interface(self, master):

        #frame = Frame(master, bd=1, pady=5, padx=2,  relief=RIDGE)

        OPTIONS = [
            "GS-ID",
            "Datum",
            "Besitzer",
            "Preis",
            "Verkaufsschild",
            "Status"
        ]

        #column 1
        Label(master, text="GS-ID").grid(row=0, column=0, padx=5, sticky=SW)
        self.entry_ID = Entry(master)
        self.entry_ID.grid(row=1, column=0)
        self.button_show = Button(master, text="Details", width=15, command=self.show_details)
        self.button_show.grid(row=3, column=0)

        Label(master, text="Besitzer:").grid(row=4, column=0, padx=5, sticky=SW)
        Label(master, text="Datum:").grid(row=5, column=0, padx=5, sticky=SW)
        Label(master, text="Preis:").grid(row=6, column=0, padx=5, sticky=SW)
        Label(master, text="Verkaufsschild:").grid(row=7, column=0, padx=5, sticky=SW)
        Label(master, text="Status:").grid(row=8, column=0, padx=5, sticky=SW)
        Label(master, text="Member:").grid(row=9, column=0, padx=5, sticky=SW)

        #column 2
        Label(master, text="Feld").grid(row=0, column=1, padx=5, sticky=SW)
        self.var_options = StringVar(master)
        self.var_options.set(OPTIONS[1])
        self.option = OptionMenu(master, self.var_options, *OPTIONS)
        self.option.grid(column=1, row=1)
        self.button_undo = Button(master, text="rueckgaengig", width=15)
        self.button_undo.grid(row=3, column=1)


        self.l1 = Label(master, text="")
        self.l1.grid(row=4, column=1, padx=5, sticky=SW)

        self.l2 = Label(master, text="")
        self.l2.grid(row=5, column=1, padx=5, sticky=SW)
        self.l3 = Label(master, text="")
        self.l3.grid(row=6, column=1, padx=5, sticky=SW)
        self.l4 = Label(master, text="")
        self.l4.grid(row=7, column=1, padx=5, sticky=SW)
        self.l5 = Label(master, text="")
        self.l5.grid(row=8, column=1, padx=5, sticky=SW)
        self.l6 = Label(master, text="")
        self.l6.grid(row=9, column=1, padx=5, sticky=SW)

        #column3
        Label(master, text="Neuer Wert").grid(row=0, column=2, padx=5, sticky=SW)
        self.entry_new = Entry(master)
        self.entry_new.grid(column=2, row=1)

        self.button_apply = Button(master, text="anwenden", width=15)
        self.button_apply.grid(row=3, column=2)

        #functionality
        self.entry_ID.insert(10, self.entryID_default)
        self.button_apply.bind('<ButtonPress-1>', self.apply)
        self.button_undo.bind('<ButtonPress-1>', self.undo)
        #self.button_show.bind('<ButtonPress-1>', self.show_details)

        #return frame

    def show_details(self):
        self.ID = self.entry_ID.get()
        if self.ID in self.data.keys():
            owner = self.data[self.ID]["Besitzer"]
            off = self.data[self.ID]["Offlinezeit"]
            prize = self.data[self.ID]["Preis"]
            sellable = self.data[self.ID]["Verkaufsschild"]
            members = self.data[self.ID]["Mitbewohner"]


            if self.data[self.ID]["Status"] == "b":
                status = "bebaut"
            elif self.data[self.ID]["Status"] == "l":
                status = "unbebaut"
            elif self.data[self.ID]["Status"] == "x":
                status = "zum Abriss"
            else:
                status = self.data[self.ID]["Status"]


            self.l1.configure(text=owner)
            self.l2.configure(text=off)
            self.l3.configure(text=prize)
            self.l4.configure(text=sellable)
            self.l5.configure(text=status)
            self.l6.configure(text=members)

        else:
            None

    def undo(self, event):
        self.handler.write(str(self.row), self.field, self.backup[self.field])
        self.data[self.ID][self.field] = self.backup[self.field]
        self.show_details()

    def apply(self, event):

        mapping={
            "Datum":"Offlinezeit",
            "GS-ID":"ID",
            "Besitzer":"Besitzer",
            "Preis":"Preis",
            "Verkaufsschild":"Verkaufsschild",
            "Status":"Status"
        }

        self.ID = self.entry_ID.get()
        self.val = self.entry_new.get()
        self.field = mapping[self.var_options.get()]

        if self.field == "ID":
            if not self.access:
                win = Tk()
                win.title("Passwort eingeben:")
                pw_win = Frame(win, width=200, height=10)

                def _check_pw(event):
                    entry = self.entry_pw.get()
                    pw = "_ysbiuQ"
                    if pw == entry:
                        self.access = True
                        print("Access granted.")
                    else:
                        self.access = False
                        print("Entered wrong password...")

                    win.destroy()


                self.entry_pw = Entry(win)
                self.entry_pw.pack(fill=BOTH)
                self.entry_pw.bind('<Return>', _check_pw)

                if not self.access:
                    return

        elif self.field == "Offlinezeit":

            if 'd' in self.val:
                def _comp_days():
                    days = re.findall(r'\dd', self.val)
                    weeks = re.findall(r"\dw", self.val)
                    if days:
                        days = int(days[0][0])
                    else:
                        days = 0
                    if weeks:
                        weeks = int(weeks[0][0])
                    else:
                        weeks = 0
                    dif = days + (weeks*7)
                    return dif

                today = datetime.date.today()
                newData = today - datetime.timedelta(days=_comp_days())
                self.val = '=TO_DATE(DATEVALUE("'+str(newData)+'"))'
                self.input_option = "USER_ENTERED"
        else:
            self.input_option = "RAW"


        if self.ID in self.data.keys():
            self.row = self.data[self.ID]["row"]
            self._make_backup()
            self.handler.write(str(self.row), self.field, self.val, self.input_option)
            self.data[self.ID][self.field] = self.val
            self.show_details()
        else:
            None

    def _make_backup(self):
            temp = self.data[self.ID]
            self.backup = temp.copy()

class SearchWindow(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.master = master
        self.master.title("Spielersuche")
        self.handler = SpreadsheetHandler()
        self.data = self.handler.load_data()
        self.create_interface(master)
        self.input_option = "RAW"
        self.player = -1
        self.foundAsOwner = []
        self.foundAsMember = []



    def create_interface(self, master):

        #frame = Frame(master, bd=1, pady=5, padx=2,  relief=RIDGE)


        #column 1
        Label(master, text="Spielername:").grid(row=0, column=0, padx=5, sticky=SW)
        self.entry_player = Entry(master)
        self.entry_player.grid(row=1, column=0)


        #column 2
        self.button_search = Button(master, text="suchen", width=15)
        self.button_search.grid(row=1, column=1)


        self.l1 = Label(master, text="")
        self.l1.grid(row=4, column=0, padx=5, sticky=SW)

        self.l2 = Label(master, text="")
        self.l2.grid(row=6, column=0, padx=5, sticky=SW)

        self.button_search.bind('<ButtonPress-1>', self.show_details)


    def show_details(self, event):

        self.player = self.entry_player.get()



        for region in self.data.keys():
            if self.player.lower() == self.data[region]["Besitzer"].lower():
                self.foundAsOwner.append(region)

            if self.player.lower() in self.data[region]["Mitbewohner"].lower():
                self.foundAsMember.append(region)

        if self.foundAsOwner == []:
            owner = "Kein Besitzer eines GS."
        else:
            owner = "Spieler besitzt folgende GS: " + str(self.foundAsOwner)[1:-1]

        if self.foundAsMember == []:
            member = "Ist nirgends als Member eingetragen."
        else:
            member = "Spieler ist auf folgende GS eingetragen: " + str(self.foundAsMember)[1:-1]

        #self.create_interface(self.master)

        self.l1.configure(text=owner)
        self.l2.configure(text=member)

        self.foundAsMember = []
        self.foundAsOwner = []




#r = Tk()
#r.withdraw()
#r.clipboard_clear()
#r.clipboard_append('i can has clipboardz?')
#r.destroy()

root = Tk()
app = MainWindow(root)
root.mainloop()
