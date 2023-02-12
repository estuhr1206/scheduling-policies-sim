#!/usr/bin/env python
"""object for instance of the breakwater logic at the server in the breakwater system."""

import random

class BreakwaterServer:

    def __init__(self, RTT, ALPHA, BETA, TARGET_DELAY):

        self.RTT = RTT
        self.target_delay = TARGET_DELAY
        self.total_credits = 0
        self.credits_issued = 0
        # this will get updated by register
        self.num_clients = 0
        self.clients = []
        self.AGGRESSIVENESS_ALPHA = ALPHA
        self.BETA = BETA
        self.overcommitment_credits = 0

    def control_loop(self, max_delay=0):

        # total credit pool
        uppercase_alpha = max(int(self.AGGRESSIVENESS_ALPHA * self.num_clients), 1)

        if max_delay < self.target_delay:
            self.total_credits += uppercase_alpha
        else:
            reduction = max(1.0 - self.BETA*((max_delay - self.target_delay)/self.target_delay), 0.5)
            self.total_credits = self.total_credits * reduction

        # overcommitment
        total_minus_issued = self.total_credits - self.credits_issued
        self.overcommitment_credits = max(int(total_minus_issued / self.num_clients), 1)

        # per client
        # random distribution for now, so no demand tracking of clients
        total_overcommitment = self.overcommitment_credits * self.num_clients
        pool_plus_overcommitment = total_overcommitment + self.total_credits

        credits_to_send = pool_plus_overcommitment - self.credits_issued
        self.send_credits(credits_to_send)







    def send_credits(self, credits_to_send):
        if credits_to_send > 0:
            potential_clients = []
            for client in self.clients:
                if client.current_demand > 0:
                    potential_clients.append(client)
            for client in potential_clients:
                client.credits += 1
                self.credits_issued += 1

        elif credits_to_send < 0:
            """
                When Ctotal decreases, the server does
                not issue additional credits to the clients, or if the clients have
                unused credits, the server sends negative credits to revoke the
                credits issued earlier. 
            """
            # Idea 1, definitive number of tries
            # probably won't revoke total number of credits, but, it does mimic
            # the paper in that it attempts to revoke that number of credits.
            for i in range(credits_to_send):
                chosen_client = random.choice(self.clients)
                if chosen_client.credits > 0:
                    chosen_client.credits -= 1
                    self.credits_issued -= 1

    def client_register(self, client):
        self.clients.append(client)
        self.num_clients += 1
        """
            I don't think this should distribute credits? 
            credit distribution should not be instantaneous, even if there were credits to grant
            to this client.

            It should happen when the control loop runs, every RTT. 
            normally, credits could be sent on the register response, but we don't really have a concept of this here

            the next RTT truly is the soonest that response could arrive regardless, so this should track
        """

    def client_deregister(self, client):
        # credits yielded by client
        self.credits_issued += client.credits

        client.registered = False
        client.credits = 0
        self.clients.remove(client)



