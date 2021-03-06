'''
Created on 2016/9/20

:author: hubo
'''
from __future__ import print_function
from vlcp.server import main
from vlcp.event import Client
from vlcp.server.module import Module
from vlcp.config import defaultconfig
from vlcp.protocol.zookeeper import ZooKeeper, ZooKeeperConnectionStateEvent,\
    ZooKeeperWatcherEvent
import vlcp.utils.zookeeper as zk
from vlcp.utils.zkclient import ZooKeeperClient, ZooKeeperSessionStateChanged
from vlcp.event.runnable import RoutineContainer
from namedstruct import dump
from pprint import pprint

@defaultconfig
class TestModule(Module):
    _default_serverlist = ['tcp://localhost:3181/','tcp://localhost:3182/','tcp://localhost:3183/']
    def __init__(self, server):
        Module.__init__(self, server)
        self.apiroutine = RoutineContainer(self.scheduler)
        self.client = ZooKeeperClient(self.apiroutine, self.serverlist)
        self.connections.append(self.client)
        self.apiroutine.main = self.main
        self.routines.append(self.apiroutine)
    def watcher(self):
        watcher = ZooKeeperWatcherEvent.createMatcher()
        while True:
            yield (watcher,)
            print('WatcherEvent: %r' % (dump(self.apiroutine.event.message),))
    def main(self):
        def _watch(w):
            for m in w.wait(self.apiroutine):
                yield m
            print('Watcher returns:', dump(self.apiroutine.retvalue))
        def _watchall(watchers):
            for w in watchers:
                if w is not None:
                    self.apiroutine.subroutine(_watch(w))
        self.apiroutine.subroutine(self.watcher(), False, daemon = True)
        up = ZooKeeperSessionStateChanged.createMatcher(ZooKeeperSessionStateChanged.CREATED, self.client)
        yield (up,)
        print('Connection is up: %r' % (self.client.currentserver,))
        for m in self.client.requests([zk.create(b'/vlcptest', b'test'),
                                       zk.getdata(b'/vlcptest', True)], self.apiroutine):
            yield m
        print(self.apiroutine.retvalue)
        pprint(dump(self.apiroutine.retvalue[0]))
        _watchall(self.apiroutine.retvalue[3])
        for m in self.apiroutine.waitWithTimeout(0.2):
            yield m
        for m in self.client.requests([zk.delete(b'/vlcptest'),
                                        zk.getdata(b'/vlcptest', watch = True)], self.apiroutine):
            yield m
        print(self.apiroutine.retvalue)
        pprint(dump(self.apiroutine.retvalue[0]))
        _watchall(self.apiroutine.retvalue[3])
        for m in self.client.requests([zk.multi(
                                        zk.multi_create(b'/vlcptest2', b'test'),
                                        zk.multi_create(b'/vlcptest2/subtest', 'test2')
                                    ),
                                  zk.getchildren2(b'/vlcptest2', True)], self.apiroutine):
            yield m
        print(self.apiroutine.retvalue)
        pprint(dump(self.apiroutine.retvalue[0]))
        _watchall(self.apiroutine.retvalue[3])
        for m in self.client.requests([zk.multi(
                                        zk.multi_delete(b'/vlcptest2/subtest'),
                                        zk.multi_delete(b'/vlcptest2')),
                                  zk.getchildren2(b'/vlcptest2', True)], self.apiroutine):
            yield m
        print(self.apiroutine.retvalue)
        pprint(dump(self.apiroutine.retvalue[0]))
        _watchall(self.apiroutine.retvalue[3])
        
        
if __name__ == '__main__':
    main()
    