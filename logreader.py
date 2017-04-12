import os

class Logreader():

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
                members = line[1]

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

        print(gs)
        print("TEST")

