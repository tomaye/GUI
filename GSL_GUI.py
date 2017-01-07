#! /usr/bin/env python3

from tkinter import *
import requests
import csv
import io
import os


def resource_path(relative_path):
     if hasattr(sys, '_MEIPASS'):
         return os.path.join(sys._MEIPASS, relative_path)
     return os.path.join(os.path.abspath("."), relative_path)



class Window(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.version = "v.1.21"
        self.master = master
        self.master.title("GSL GUI "+"\t"+ self.version)
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
                #print(temp)
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

    def draw_rect(self, master, id, singleSearch=False, multiSearch=False, showAll=False, demolish=False):

        if singleSearch:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="orange", tags=id)

        elif multiSearch:
            if showAll:
                master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="pink", tags=id)
            else:
                master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="green", tags=id)
        elif demolish:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], fill="red", tags=id)
        else:
            master.create_rectangle(self.data[id]["x0"], self.data[id]["y0"], self.data[id]["x1"], self.data[id]["y1"], tags=id, fill="white", stipple="gray12")

    def create_canvas(self, master):

            self.canv = Canvas(master, width=604, height=604, relief=SUNKEN)
            img = resource_path("bg_GUI.png")
            self.map = PhotoImage(file=img)
            self.canv.create_image(304, 295, image=self.map)
            for id in self.data.keys():

                def make_lambda(x, hide):
                    return lambda ev: self.display_info(x, hide)
                self.widgets[id] = self.draw_rect(self.canv, id)
                self.canv.tag_bind(id, '<Enter>', make_lambda(id, False))
                self.canv.tag_bind(id, '<Leave>', make_lambda(id, True))

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
                building = self.data[id]["Offlinezeit"]
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

        sellable = _ids_in_range(sellable)
        ownedByCity = _ids_in_range(ownedByCity)

        b = self.var_bebaut.get()
        l = self.var_unbebaut.get()
        if l and not b:
            unbebaut = _has_building(sellable, True)
            sellable = unbebaut
        elif b and not l:
            bebaut = _has_building(sellable)
            sellable = bebaut
        elif b and l:
            bebaut = _has_building(sellable)
            unbebaut = _has_building(sellable, True)
            sellable = unbebaut + bebaut

        if self.var_abriss.get():
            sellable = []
            ownedByCity = []
            self.canv.destroy()
            self.canvas = self.create_canvas(self.master)
            self.canvas.pack()
            for gs in self.data.keys():
                if self.data[gs]["Offlinezeit"].lower() == "x":
                    self.draw_rect(self.canv, gs, False, False, False, True)

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

root = Tk()
app = Window(root)
root.mainloop()

k=input("Press enter to exit ")