import os
import cmd
import types
import readline
import platform
import shlex

py_ver = platform.python_version_tuple()
if int(py_ver[0]) == 2 and int(py_ver[1]) < 5:  # python version is 2.4.x
    from process_management import call, CalledProcessError
else:
    from subprocess import call, CalledProcessError


from gsh_common import CommandHandler
from gsh_grid import getSiteNameFromFQDN, buildGlobusPing
import gsh_version

class Console(cmd.Cmd):
    def __init__(self, site):
        cmd.Cmd.__init__(self)
        self.suffix = "=>> "
        self.intro = "Welcome to gsh! "

        self.prompt = site + " " + self.suffix
        self.keywords = ["!", "hist", "exit", "help", "setsite", "getsite",
                         "EOF", "vdt_location", "version"]
        self.home = os.environ['HOME']
        self.history = "%s/.gsh_history" % self.home
        self.workfile = "%s/gsh_workfile" % self.home

        call(["/bin/touch", self.workfile])
        call(["/bin/touch", self.history])

        # site specific variables
        self.site_env = {}

        self.site = site
        self.site_name = getSiteNameFromFQDN(self.site)
        # register command handler
        self.commandHandler = CommandHandler(self)

        pwd = self.commandHandler.get_pwd(empty_cwd=True)
        self.cwd = pwd.split("/")

    def set_cwd(self, path):
        self.cwd = path.split("/")
        self.prompt = "%s %s %s" % (self.site, self.cwd[-1], self.suffix)

    ## Command definitions to support Cmd object functionality ##
    def do_EOF(self, args):
        """Exit on system end of file character"""
        readline.write_history_file(self.history)
        call(["/bin/rm", "-f", self.workfile])

        return self.do_exit(args)

    def do_shell(self, args):
        """Pass command to a system shell when line begins with '!'"""
        if isinstance(args, types.StringType):
            args = shlex.split(args)
        call(args, env=os.environ)

    def do_help(self, args):
        """Get help on commands
           'help' or '?' with no arguments prints a list of commands for which help is available
           'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)

    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion
        # need to read history and set self._hist
        f = open(self.history)
        hist = f.readlines()
        f.close()
        self._hist = [a[:-1] for a in hist]
        readline.read_history_file(self.history)
        self._locals = {}      ## Initialize execution namespace for user
        self._globals = {}

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modify the input line
            before execution (for example, variable substitution) do it here.
        """
        self._hist += [ line.strip() ]
        if len(line) > 1: # added so that gsh doesn't bomb when user presses enter without typing anything else
            if not (line.split()[0] in self.keywords):
                if len(self.site) < 1:
                    print "You did not specify a site.  Please execute setsite <fqdn> with a valid fqdn."
                    line = ""
                else:
                    line = self.commandHandler.customCommand(line, self.workfile)

        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """
        return stop

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        try:
            exec(line) in self._locals, self._globals
        except Exception, e:
            print e.__class__, ":", e

    def get_env(self, var):
        return self.site_env[var]

    def set_env(self, var, val):
        if val:
            self.site_env[var] = val
        else:
            # if empty val is passed we will clear it out of the env
            try:
                self.site_env.pop(var)
            except:
                # var didn't exist, but since were were clearing it anyway
                # we don't care, doing it this way, so that there is only one
                # hash table lookup instead of two.
                pass

    ## Command definitions ##
    def do_hist(self, args):
        """Print a list of commands that have been entered"""
        print self._hist

    def do_exit(self, args):
        """Exits from the console"""
        return -1

    def do_setsite(self, args):
        """
        Sytnax:

        =>> setsite fqdn

        Description:

        Sets the fully qualified domain name (fqdn) of a desired site.
        All entered commands will be run on this site.

        There can only be one...
        """
        if len(args) == 0:
            print "setsite must follow the folowing format:  setsite <fqdn>"
        else:
            old_site = self.site
            self.site = args
            globus_ping = buildGlobusPing(self.site)
            try:
                _ = self.commandHandler.run(globus_ping)
                # the ping result succeeded so, set everything up for the new site
                self.prompt = self.site + " " + self.suffix
                self.site_env = {}
                self.site_name = getSiteNameFromFQDN(self.site)
            except OSError, oe:
                print "ERROR.  The globus client is not in the path."
            except CalledProcessError, cpe:
                # the ping failed so restore the old site
                print "You are not authorized to run at %s restoring the old" \
                      " site setting." % self.site
                print cpe.output
                self.site = old_site

    def do_getsite(self, args):
        """
        Sytnax:

        =>> getsite

        Description:

        Gets the fully qualified domain name (fqdn) of the site where
        entered commands will be run.  Also queries MyOSG to get the
        OIM site name for the fqdn.

        There can only be one...
        """
        print self.site

    def do_vdt_location(self, args):
        """
        Sytnax:

        =>> vdt_location

        Description:

        Displays the VDT location

        """
        if self.site_env.has_key("VDT_LOCATION"):
            if self.site_env["VDT_LOCATION"] == "":
                self.site_env["VDT_LOCATION"] = self.commandHandler.get_vdt_location()
                self.site_env["VDT_LOCATION"] = self.site_env["VDT_LOCATION"].strip()
        else:
            self.site_env["VDT_LOCATION"] = self.commandHandler.get_vdt_location()
            self.site_env["VDT_LOCATION"] = self.site_env["VDT_LOCATION"].strip()

        print self.site_env["VDT_LOCATION"]

    def do_version(self, args):
        """
        Sytnax:

        =>> version

        Description:

        Displays the gsh software version

        """
        print "%s.%s.%s" % (gsh_version.MAJOR, gsh_version.MINOR, gsh_version.PATCH)

