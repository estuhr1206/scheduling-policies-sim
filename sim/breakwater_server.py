#!/usr/bin/env python
"""object for instance of the breakwater logic at the server in the breakwater system."""


class BreakwaterServer:

    def __init__(self, RTT):

        self.RTT = RTT
        self.total_credits = 0
        # this will get updated by register
        self.num_clients = 0

    def control_loop(self, max_delay=0):
        pass

    def send_credit(self):

        # will give a credit to a random client who has demand
        pass

    def client_register(self):

        self.num_clients += 1
        pass

