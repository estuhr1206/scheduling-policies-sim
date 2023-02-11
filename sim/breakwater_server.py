#!/usr/bin/env python
"""object for instance of the breakwater logic at the server in the breakwater system."""


class BreakwaterServer:

    def __init__(self, RTT):

        self.RTT = RTT
        self.total_credits = 0
        # this will get updated by register
        self.num_clients = 0
        self.clients = []

    def control_loop(self, max_delay=0):
        pass

    def send_credit(self):

        # will give a credit to a random client who has demand
        pass

    def client_register(self, client):
        self.clients.append(client)
        self.num_clients += 1

    def client_deregister(self, client):
        # looking through whole list isn't great, but keeps the logic simple for now

        pass

        """
            I don't think this should distribute credits? 
            credit distribution should not be instantaneous, even if there were credits to grant
            to this client.
            
            It should happen when the control loop runs, every RTT. 
            normally, credits could be sent on the register response, but we don't really have a concept of this here
            
            the next RTT truly is the soonest that response could arrive regardless, so this should track
        """

