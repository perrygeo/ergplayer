import time
import Tkinter as tk

class ErgFile:
    def __init__(self, filename):
        self.filename = filename
        fh = open(filename)
        erg_lines = fh.readlines()
        fh.close()
        self.header, self.data = self.parse_erg(erg_lines)
    
    def parse_erg(self, erg_lines):
        erg_lines = [x.strip() for x in erg_lines]
        if erg_lines[0] != "[COURSE HEADER]":
            raise Exception("Must start with [COURSE HEADER]")
        in_header = True
        linenum = 1
        header = {}
        while in_header:
            line = erg_lines[linenum]
            linenum+=1
            if line.strip() == '': 
                continue
            if line == "[END COURSE HEADER]":
                in_header = False
                continue
            if "=" in line:
                k, v = [x.strip() for x in line.split("=")]
                header[k] = v
            else:
                time_units, power_units = [x.strip() for x in line.split()]
                header["time_units"] = time_units
                header["power_units"] = power_units

        in_data = False
        while not in_data:
            if erg_lines[linenum] == "[COURSE DATA]":
                in_data = True
            linenum+=1

        data = []
        while in_data:
            if linenum >= len(erg_lines)-1:
                break
            start = erg_lines[linenum]
            end = erg_lines[linenum+1]
            linenum+=2
            if start == '' or end == '': 
                continue
            if start == "[END COURSE DATA]" or end == "[END COURSE DATA]":
                in_data = False
                continue
            stime, spower = [float(x.strip()) for x in start.split()]
            etime, epower = [float(x.strip()) for x in end.split()]
            data.append( (stime, etime, spower, epower) )
            
        return header, data

    def beep(self):
        #print chr(7)
        self.root.bell()

    def update_display(self):
        if abs(self.power - self.last_beep_power) >= self.beep_threshold:
            self.last_beep_power = self.power
            self.beep()
    
        if self.segment_beep and self.segment_remaining < 3:
            self.beep()

        output = ' '.join(str(x) for x in [self.message, self.segment_remaining, self.total_remaining, self.power, self.header['power_units']])
        self.power_label['text'] = str(self.power)
        self.message_label['text'] = self.message
        self.segrem_label['text'] =  self.sec2hms(self.segment_remaining)
        self.totalrem_label['text'] = self.sec2hms(self.total_remaining)
        self.root.update()

    def countdown(self,sec=1):
        self.update_display()
        self.segment_remaining-=sec
        self.total_remaining-=sec
        time.sleep(sec)
        self.root.update()

    def setup_gui(self):
        # set up GUI
        self.root = tk.Tk()

        self.message_label = tk.Label(self.root, text='Waiting........', font=("Helvetica",20))
        self.power_label = tk.Label(self.root, text='000', font=("Helvetica", 156))
        self.units_label = tk.Label(self.root, text=self.header['power_units'], font=("Helvetica", 36))
        self.segrem_header = tk.Label(self.root, text='\n\nTime remaining in interval:', font=("Helvetica",20))
        self.segrem_label = tk.Label(self.root, text=':', font=("Helvetica",40))
        self.totalrem_header = tk.Label(self.root, text='Time remaining (total):', font=("Helvetica",20))
        self.totalrem_label = tk.Label(self.root, text=':', font=("Helvetica",40))

        self.message_label.pack()
        self.power_label.pack()
        self.units_label.pack()
        self.segrem_header.pack()
        self.segrem_label.pack()
        self.totalrem_header.pack()
        self.totalrem_label.pack()

        # gracefully handle Xing out the window
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        
    def sec2hms(self,seconds):
        hours = seconds / 3600
        seconds -= 3600*hours
        minutes = seconds / 60
        seconds -= 60*minutes
        if hours == 0:
            return "%02d:%02d" % (minutes, seconds)
        return "%02d:%02d:%02d" % (hours, minutes, seconds)

    def play(self, warmup=None, cooldown=None):
        # set up 
        self.setup_gui()
        self.beep_threshold = 5 
        self.last_beep_power = 0
        self.segment_beep = True
        if self.header['time_units'].lower() == "minutes":
            self.workout = int(self.data[-1][1] * 60.)
            self.total_remaining = self.workout
        else:
            raise Exception("Cant convert ...  dont know time units")

        if warmup:
            self.warmup = int(warmup * 60.)
            self.total_remaining += self.warmup
        if cooldown:
            self.cooldown = int(warmup * 60.)
            self.total_remaining += self.cooldown
        self.power = 0
        self.message = ''

        # Run warmup
        if warmup:
            self.segment_remaining = self.warmup
            self.message = "Warming up" 
            for i in range(self.warmup):
                self.countdown()
                
        # Run main workout
        self.message = "Workout"
        for d in self.data:
            if self.header['time_units'].lower() == "minutes":
                self.current_seg = int((d[1]-d[0]) * 60.)
            else:
                raise Exception("Cant convert ...  dont know time units")
                
            self.segment_remaining = self.current_seg
            for i in range(self.current_seg):
                ratio = float(self.segment_remaining) / float(self.current_seg)
                self.power = int(d[3] - (d[3]-d[2]) * ratio)
                self.countdown()
            
        # Run cooldown
        if cooldown:
            self.segment_remaining = self.cooldown
            self.message = "Warming up" 
            for i in range(self.warmup):
                self.countdown()


def test():
    #erg = ErgFile('test_data/MAX_VO2_TEST.erg')
    erg = ErgFile('test_data/SST_ramp.erg')
    erg.play(warmup=0.05, cooldown=0.1)

if __name__ == "__main__":
    test()

