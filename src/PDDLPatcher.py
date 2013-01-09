from InitFileMgr import *
import pdb

class PDDLPatcher:
    def __init__(self, pddlFile):
        self.initFileMgr = InitFileMgr(pddlFile)

    def patchWithFFOutput(self, ffOutputFile, stateNum):
        print "Patching with state {0} from {1}.\n".format\
            (stateNum, ffOutputFile)
        op = OutputParser(ffOutputFile)
        propSet = op.getPropSet()

        deltaState = op.getStateByIndex(stateNum)

        #deltaState.printState()
        ##Compile away FF's CWA: figure out the set of props
        ## it has CWA with, include those not in true set as false
        deltaState.makeCWAExplicit(propSet)
        self.initFileMgr.patchInitState(deltaState)

    def patchWithProps(self, inputFromContinuous):
        ## Suppose inputFromContinuous is a set of 
        ## propositions to be added to the state
        
        ## Should work with prop-literals of the form
        ## (not-p x) as well
        print "Patching with props: "
        print inputFromContinuous
        print
        deltaState = State()
        map(lambda x: deltaState.addProposition(x), inputFromContinuous)
        self.initFileMgr.patchInitState(deltaState)


    def patchStateNumWithProps(self, stateNum, ffOutputFile,\
                                   factsFromContinuous):
        ## first get initFileMgr to the right state num
        self.initFileMgr.rollbackTo(0)
        self.patchWithFFOutput(ffOutputFile, stateNum)
        self.patchWithProps(factsFromContinuous)
    

    def patchWithNewInterpretation(self, symbol, factsFromContinuous):
        self.initFileMgr.purgeFactsWithSymbol(symbol)
        self.patchWithProps(factsFromContinuous)


    def printInitState(self):
        self.initFileMgr.printInitState()

    def writeCurrentInitState(self, ofname):
        self.initFileMgr.writeCurrentPDDL(ofname)


if __name__ == "__main__":
    # mypatcher = PDDLPatcher("/tmp/test2.out")
    # myPatcher.printInitState()
    # myPatcher.patchWithFFOutput("/tmp/test.out", 4)
    # myPatcher.printInitState()
    # myPatcher.writeCurrentInitState("/tmp/test3.out")
    # myPatcher.patchWithProps(["(a b c)"])
    # myPatcher.printInitState()
    
    # myPatcher.patchStateNumWithProps(0, "/tmp/test.out", ["(start obj1)"])
    # myPatcher.printInitState()
    
    # myPatcher.patchWithNewInterpretation("p1", ["(x p1 p2)"])
    # myPatcher.printInitState()
    path = "/Users/Sid/work/Planners/myDomains/"

    myPatcher = PDDLPatcher(path+"robotics_autogen_prob.pddl")
    myPatcher.printInitState()
    
    errorStr = open(path+"robotics_autogen_err1.txt").read()
    
    errorLines = errorStr.lower().split("\n")

    failedActionNumber = int(errorLines[0].strip("linenumber: "))
    propList = errorLines[1:]
    
    myPatcher.patchWithFFOutput(path+"robotics_autogen_plan1.pddl", \
                                    failedActionNumber-1)
    myPatcher.printInitState()
    myPatcher.patchWithProps(propList)
    myPatcher.printInitState()
    myPatcher.writeCurrentInitState(path + "robotics_autogen_prob2.pddl")

    errorStr = open(path+"robotics_autogen_err2.txt").read()
    errorLines =  errorStr.lower().split("\n")
    failedActionNumber = int(errorLines[0].strip("linenumber: "))
    propList = filter(lambda x: len(x)>0, errorLines[1:])
    
    myPatcher.patchWithFFOutput(path+"robotics_autogen_plan2.pddl", \
                                    failedActionNumber-1)
    myPatcher.printInitState()
    myPatcher.patchWithProps(propList)
    myPatcher.printInitState()
    myPatcher.writeCurrentInitState(path + "robotics_autogen_prob3.pddl")
