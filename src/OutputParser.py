
stateListDelimiter = "*** States ***"
stateDelimiter = "State"

from State import *
import re,sys,pdb
propPattern = re.compile("\(.*\)\Z")


def tryOpen(fname, mode):
    try:
        fhandle = open(fname, mode)
    except IOError as e:
        print "\nWhile opening {0}".format(fname)
        print "Encountered IO Error {0}: {1}".format(e.errno, e.strerror)
        print "Ending process. \n"
        sys.exit(-1)

    return fhandle


def tryIO(fname, mode, strBufPtr=""):
    '''tries to open file in appropriate mode and do I/O.
    mode can be "read" or "write". 
    returns the read buffer if mode is read, and return value of f.write() 
    if mode is write.''' 

    try:
        if mode == "read":
            fhandle = open(fname, "r")
            strBufPtr = fhandle.read()
            retVal = strBufPtr
        if mode == "write":
            fhandle = open(fname, "w")
            retVal = fhandle.write(strBufPtr)
    except IOError as e:
        print "While working on {0}".format(fname)
        print "Encountered IO Error {0}: {1}".format(e.errno, e.strerror)
        print "Ending process. \n"
        sys.exit(-1)
    finally:
        fhandle.close()
        
    return retVal
        

class OutputParser:
    def __init__(self, fname):
        self.fname = fname
        self.stateList = []
        self.propSet = set()
        print "Setting up FF o/p parser for {0}.".format(fname)
        if fname != "":
            self.parseFFOutput("")

    def parseFFOutput(self, fileStr):
        ''' returns list of states from fileStr.
        First state in the list is the state before 
        the first action.'''

        if self.fname != "":
            #f = tryOpen(self.fname, "r")
            #fstr = f.read()
            #f.close()
            
            fstr = tryIO(self.fname, "read")
            relevantStr = fstr.split(stateListDelimiter)[1]
        
        if fileStr != "":
            fstr = fileStr
            relevantStr = fstr

        stateList = []
        
        for stateStr in relevantStr.split(stateDelimiter):
            s = self.getStateFromStr(stateStr)
            if s.size() >0:
                stateList.append(s)
        self.stateList = stateList
        return stateList


    def getStateFromStr(self, stateStr):
        s = State()
        for rawPropositionStr in stateStr.split("\n"):
            propositionStr = rawPropositionStr.strip().replace(\
                "(", " ").replace(")", " ").lower()
            propositionStr = "("+propositionStr.strip()+")"
            if propositionStr != "()":
                if propPattern.match(propositionStr) != None:
                    s.addProposition(propositionStr)
                else:
                    print "not a proposition: " + propositionStr
        return s


    def getPropSet(self):
        stateProps = self.stateList[0].getAllProps()
        sProps = stateProps
        for state in self.stateList:
            prevStateProps = stateProps
            stateProps = state.getAllProps()
            diff = prevStateProps^stateProps 
            # if len(diff) >0:
            #     print "diffs from previous:"
            #     print "diff: "+ str(diff)+"\n\n"
            sProps = sProps|stateProps

        return sProps

    def getStateByIndex(self, index):
        if len(self.stateList) > index +1:
            return self.stateList[index]
        else:
            print "Error: state index out of range"
            return -1

    def getFFPlan(self):
        ffstr = tryIO(self.fname, "read")

        ffPlanStr = ffstr.split("found legal plan as follows")[1].\
            split("time")[0]
        return ffPlanStr.replace("step", "")


                
            
        

        
    