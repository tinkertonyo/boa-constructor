#
# Instant Python
# $Id$
#
# process python commands line by line
#
# written by Fredrik Lundh, November 1996
#
# fredrik@pythonware.com
# http://www.pythonware.com
#


import string, sys, traceback

sys.ps1 = ">>> "
sys.ps2 = "... "

class PythonInterpreter:

    def __init__(self, name = "<console>"):

        self.name = name
        self.locals = {}

        self.lines = []

    def push(self, line):

        #
        # collect lines

        if self.lines:
            if line:
                self.lines.append(line)
                return 1 # want more!
            else:
                line = string.join(self.lines, "\n") + "\n"
        else:
            if not line:
                return 0

        #
        # compile what we've got this far

        try:
            if sys.version_info[:2] >= (2, 2):
                import __future__
                code = compile(line, self.name, "single", 
                               __future__.generators.compiler_flag, 1)
            else:
                code = compile(line, self.name, "single")
            self.lines = []

        except SyntaxError, why:
            if why[0] == "unexpected EOF while parsing":
                # start collecting lines
                self.lines.append(line)
                return 1 # want more!
            else:
                self.showtraceback()

        except:
            self.showtraceback()

        else:
            # execute
            try:
                exec code in self.locals
            except:
                self.showtraceback()

        return 0

    def showtraceback(self):

        self.lines = []

        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type == SyntaxError:# and len(sys.exc_value) == 2:
            # emulate interpreter behaviour
            if len(sys.exc_value.args) == 2:
                sys.stderr.write(" " * (sys.exc_value[1][2] + 3) + "^\n")
            sys.stderr.write("'''" + str(sys.exc_type) + " : " + \
                  str(sys.exc_value[0])+"'''\n")
        else:
            traceback.print_tb(sys.exc_traceback, None)
            sys.stderr.write("'''" + str(sys.exc_type) + " : " + \
                  str(sys.exc_value)+"'''\n")


# --------------------------------------------------------------------
# test stuff

if __name__ == "__main__":

    #
    # simple console interpreter simulation

    print 'Python', sys.version, "(PythonInterpreter)"
    print sys.copyright

    interp = PythonInterpreter()

    try:

        sys.stdout.write(sys.ps1)

        while 1:
            if interp.push(raw_input()):
                sys.stdout.write(sys.ps2)
            else:
                sys.stdout.write(sys.ps1)

    except EOFError:
        pass
