#   pimento.py
#
#   Created by Jon-Paul Diefenbach
#   Version 0.3
#   Released 1/31/2014
#
#   PiMento is a script for creating a series of sequential images to be
#   assembled into a time lapse video. The script saves to the directory
#   it is launched from by default. Since these files can accumulate
#   very quickly, we recommend putting the script on a large USB drive and
#   running it from there.
#
#   Note by default the "-t" param for raspistill is passed as "-t 1"
#   because this delays the capture by n ms and we don't want that messing
#   with the timing. By default raspistill sets -t to 5000 for a five-second
#   delay. Setting it to 1 takes the picture instantly.
#
#   Features include:
#
#   * Pass raspistill params (e.g. "-w 1600 -h 900 -awb auto") to pimento.
#   
#   * Custom params for capture interval, FPS of finished video, save
#     location, project name, and broadcast mode.
#
#   * Broadcast mode to serve up the most recent image via web as preview.png
#     to use while framing a shot.
#
#   * Precise timing.
#
#   Custom parameters:
#
#   -dir [directory]    |Sets a different save directory (Default: current)
#   -pr [project name]  |Sets different output file name (Default: frame*)
#   -i [secs]           |Sets the capture interval (Default: 6 secs.)
#   -fps [frames]       |Sets FPS of finished video. (Default: 24) NOTE: Used
#                       |for calculation only. This script does not create the
#                       |video as that would be too far too taxing on the pi.
#   -brd                |Broadcast mode. Save a copy of the current image to
#                       |/var/www/preview.png for framing a shot.
#   -brdo               |Broadcast Only mode. Serves up the preview without
#                       |recording the sequential time lapse images.
#
#   Known Issues/Bugs:
#
#   * Needs exception handling. Right now it exits on CTRL-C but will continue
#     to run through other exceptions, such as write errors caused by running
#     out of space on the drive.
#
#   * Needs to check for Apache install if trying to broadcast.
#
#   * Needs error handling for passing in incorrect raspistill params
#
#   Future Plans:
#
#   * Add a feature to stop recording after a certain elapsed time, frame
#     count, or final video length
#
#   * Integrate pycam instead of using subprocess.call to take the pictures.
#
#   * Ditch the Apache dependency for broadcast mode and instead use web.py to
#     serve up a web interface with the preview image and form buttons and
#     sliders for selecting the various settings. The goal is to be able to
#     run this on a pi headless, and set up and control time lapse recordings
#     from any device with a browser. Possibly add feature to set up pi as a
#     wifi hotspot for recording in the wild.


# Import time to handle the timing as well as format the output to "xx:xx:xx".
# Import arguments, and stdout for same-line printing of the running frame,
# duration, and final video counts. Import call to call raspistill.
import time
from sys import argv, stdout
from subprocess import call

class Session:
    """
            Parses and contains params from argv and sets up defaults and file
            names.
    """

    def __init__(self, args):
        args = args[1:]
        self.interval = 6
        self.fps = 24
        self.directory = "."
        self.name = "frame"
        self.t = 1
        self.e = ".png"
        self.params = []
        self.recording = True
        self.broadcasting = False
        self.framecount = 0
        
        while len(args) > 0:
            if args[0] == "-dir":
                args.pop(0)
                self.directory = args.pop(0)
            elif args[0] == "-pr":
                args.pop(0)
                self.name = args.pop(0)
            elif args[0] == "-i":
                args.pop(0)
                self.interval = int(args.pop(0))
            elif args[0] == "-fps":
                args.pop(0)
                self.fps = int(args.pop(0))
            elif args[0] == "-t":
                args.pop(0)
                self.t = int(args.pop(0))
            elif args[0] == "-e":
                args.pop(0)
                self.e = "." + args.pop(0)
            elif "-brd" in args[0]:
                self.broadcasting = True
                if args[0] == "-brdo":
                    self.recording = False
                args.pop(0)
            else:
                self.params.append(args.pop(0))

        self.params += ["-t", str(self.t)]
        self.fileprefix = self.directory + "/" + self.name    

# This sends the actual commands to capture, broadcast, or both, depending
# on what paramters were passed in.
def send_command(session):
    if session.recording:
        filename = session.fileprefix + str(session.framecount + 1) + session.e
        command = ["raspistill", "-o", filename] + session.params
        call(command)
        if session.broadcasting:
            command = ["cp", filename, "/var/www/preview.png"]
            call(command)
    else:
        command = ["raspistill", "-o", "/var/www/preview.png"] + session.params
        call(command)
    
# The main function to capture pictures and display info to the user. It records
# the system time just before and just after capturing the image, so the time it
# takes to capture can be subtracted from the delay interval for precise timing.
def record(session):
    starttime = time.time()
    call ("clear")
    print "Time-lapse recording started", time.strftime("%b %d %Y %I:%M:%S", time.localtime())
    print "CTRL-C to stop\n"
    print "Frames:\tTime Elapsed:\tLength @", session.fps, "FPS:"
    print "----------------------------------------"

    while True:
        routinestart = time.time()

        send_command(session)
        
        session.framecount += 1

        # This block uses the time module to format the elapsed time and final
        # video time displayed into nice xx:xx:xx format. time.gmtime(n) will
        # return the day, hour, minute, second, etc. calculated from the
        # beginning of time. So for instance, time.gmtime(5000) would return a
        # time object that would be equivalent to 5 seconds past the beginning
        # of time. time.strftime then formats that into 00:00:05. time.gmtime
        # does not provide actual milliseconds though, so we have to calculate
        # those seperately and tack them on to the end when assigning the length
        # variable. I'm sure this isn't the most elegant solution, so
        # suggestions are welcome.
        elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time()-starttime))
        vidsecs = float(session.framecount)/session.fps
        vidmsecs = str("%02d" % ((vidsecs - int(vidsecs)) * 100))
        length = time.strftime("%H:%M:%S.", time.gmtime(vidsecs)) + vidmsecs

        stdout.write("\r%d\t%s\t%s" % (session.framecount, elapsed, length))
        stdout.flush()
        time.sleep(session.interval - (time.time() - routinestart))

try:
    record(Session(argv))
except KeyboardInterrupt:
    print "\nExiting..."
