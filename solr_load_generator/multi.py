import distutils.spawn
import sys
from twisted.python import failure
from twisted.logger import Logger, globalLogBeginner, jsonFileLogObserver
from twisted.internet import protocol, error, defer, task, stdio


class KillableProcessProtocol(protocol.ProcessProtocol):
    log = Logger()

    def __init__(self, processEnded):
        self.processFinishedExecution = processEnded

    def outReceived(self, data):
        self.log.info(data)

    def errReceived(self, data):
        self.log.error(data)

    def terminate(self):
        self.transport.signalProcess('KILL')

    def processExited(self, status):
        self.processFinishedExecution.callback(status)


class RespawningProcess(object):
    running = True
    processProtocol = None
    log = Logger()

    def __init__(self, reactor, *spawnProcessArgs, **spawnProcessKWargs):
        self.reactor = reactor
        self.spawnProcessArgs = spawnProcessArgs
        self.spawnProcessKWargs = spawnProcessKWargs

    def start(self):
        self.respawn(failure.Failure(error.ProcessDone("begin")))

    def stop(self):
        self.running = False
        if self.processProtocol:
            self.processProtocol.terminate()

    def respawn(self, status):
        if self.running:
            status.trap(error.ProcessDone)

        processEnded = defer.Deferred()
        processEnded.addErrback(self.respawn)
        processEnded.addErrback(self.log.failure, "Process exited")

        self.processProtocol = KillableProcessProtocol(processEnded)
        self.reactor.spawnProcess(self.processProtocol,
                                  *self.spawnProcessArgs,
                                  **self.spawnProcessKWargs)


class ProcessCollection(object):

    def __init__(self):
        self.processes = []

    def addProcesses(self, respawningProcesses):
        self.processes.extend(respawningProcesses)

    def start(self):
        for process in self.processes:
            process.start()

    def stop(self):
        for process in self.processes:
            process.stop()


class FireOnInput(protocol.Protocol):
    fired = False

    def __init__(self, deferred):
        self.deferred = deferred

    def dataReceived(self, _):
        if not self.fired:
            self.fired = True
            self.deferred.callback(None)


def main(reactor, *argv):
    import argparse

    a = argparse.ArgumentParser()

    a.add_argument('number', type=int)
    a.add_argument('subprocess', nargs='+')

    args = a.parse_args(argv)

    globalLogBeginner.beginLoggingTo([jsonFileLogObserver(sys.stdout)])

    executablePath = distutils.spawn.find_executable(args.subprocess[0])
    args.subprocess[0] = executablePath

    collection = ProcessCollection()
    reactor.addSystemEventTrigger("before", "shutdown", collection.stop)

    processes = [RespawningProcess(reactor,
                                   executablePath, args.subprocess,
                                   usePTY=True)
                 for _ in xrange(args.number)]
    collection.addProcesses(processes)
    collection.start()

    terminationDeferred = defer.Deferred()
    stdio.StandardIO(FireOnInput(terminationDeferred))

    return terminationDeferred


task.react(main, sys.argv[1:])
