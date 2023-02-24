#!/usr/bin/env python
"""object for instance of the breakwater logic at the server in the breakwater system."""

import random

class BreakwaterServer:

    def __init__(self, RTT, ALPHA, BETA, TARGET_DELAY, state):
        self.state = state
        self.RTT = RTT
        self.target_delay = TARGET_DELAY
        self.total_credits = 50
        self.credits_issued = 0
        # this will get updated by register
        self.num_clients = 0
        self.clients = []
        self.AGGRESSIVENESS_ALPHA = ALPHA
        self.BETA = BETA
        self.overcommitment_credits = 0
        self.max_delay = 0

        self.credit_pool_records = []

        # TODO remove, debugging
        self.counter = 0

    def control_loop(self, max_delay=0):
        self.max_delay = max_delay
        # total credit pool
        uppercase_alpha = max(int(self.AGGRESSIVENESS_ALPHA * self.num_clients), 1)

        if max_delay < self.target_delay:
            self.total_credits += uppercase_alpha
        else:
            reduction = max(1.0 - self.BETA*((max_delay - self.target_delay)/self.target_delay), 0.5)
            self.total_credits = int(self.total_credits * reduction)

        credits_to_send = self.total_credits - self.credits_issued
        # overcommitment seems to allow massive amounts of credits to build up at client
        self.overcommitment_credits = max(int(credits_to_send / self.num_clients), 1)

        # TODO remove, debugging
        # self.counter += 1
        # if self.counter >= 1000:
        #     print("max_delay: {0}, pool: {1}, credits to send: {2}. overcommit: {3}".format(
        #         max_delay, self.total_credits, credits_to_send, self.overcommitment_credits
        #     ))
        #     self.counter = 0
        if self.state.config.record_credit_pool:
            self.credit_pool_records.append([self.total_credits, self.credits_issued, self.overcommitment_credits])

        if self.num_clients > 0:
            self.send_credits(int(credits_to_send))
        # TODO I think it should be interesting to see the credit pool both before and after
        # there is an attempt to issue the credits?
        if self.state.config.record_credit_pool:
            self.credit_pool_records.append([self.total_credits, self.credits_issued, self.overcommitment_credits])

    def send_credits(self, credits_to_send):

        if credits_to_send > 0:
            # idea 1: Might loop forever? but hopefully client
            # would simply deregister without fail once it has 0 demand
            # i = 0
            # while i < credits_to_send:
            #     if self.num_clients <= 0:
            #         break
            #     chosen_client = random.choice(self.clients)
            #     if chosen_client.current_demand > 0:
            #         chosen_client.add_credit()
            #         self.credits_issued += 1
            #         i += 1
            #     else:
            #         continue
                

            # idea 2: doesn't scale
            # potential_clients = []
            # for client in self.clients:
            #     if client.current_demand > 0:
            #         potential_clients.append(client)
            # if len(potential_clients) > 0:
            #     for i in range(credits_to_send):
            #         chosen_client = random.choice(potential_clients)
            #         chosen_client.add_credit()
            #         self.credits_issued += 1

            # idea 3, just give out credits regardless of demand?
            # for i in range(credits_to_send):
            #     chosen_client = random.choice(self.clients)
            #     chosen_client.add_credit()
            #     self.credits_issued += 1
            # TODO attempting to fix distribution
            i = 0
            while i < credits_to_send:
                if self.num_clients <= 0:
                    break
                chosen_client = random.choice(self.clients)
                Cx_new = min(chosen_client.current_demand + self.overcommitment_credits,
                             chosen_client.credits + (self.total_credits - self.credits_issued))
                if Cx_new - chosen_client.credits > 0:
                    chosen_client.add_credit()
                    self.credits_issued += 1
                    i += 1
                else:
                    # TODO for debugging purposes, client de registering is off right now
                    # if our single client doesn't get any credits, just stop
                    break

        elif credits_to_send < 0:
            """
                When Ctotal decreases, the server does
                not issue additional credits to the clients, or if the clients have
                unused credits, the server sends negative credits to revoke the
                credits issued earlier. 
            """
            # definitive number of tries
            # probably won't revoke total number of credits, but, it does mimic
            # the paper in that it attempts to revoke that number of credits.
            for i in range(credits_to_send):
                chosen_client = random.choice(self.clients)
                if chosen_client.credits > 0:
                    chosen_client.credits -= 1
                    self.credits_issued -= 1

            # paper implementation does not make sense for now
            # would unfairly take away lots of credits from a single client,
            # because we are not doing lazy distribution

            # Cx_new = min(chosen_client.current_demand + self.overcommitment_credits,
            #              chosen_client.credits - 1)
            #
            # credits_to_revoke = Cx_new - chosen_client.credits
            # chosen_client.credits += credits_to_revoke
            # # this should always be negative
            # if credits_to_revoke >= 0:
            #     raise ValueError('credits_to_revoke should never be positive, was {}'.format(credits_to_revoke))
            # self.credits_issued += credits_to_revoke

    def client_register(self, client):
        self.clients.append(client)
        # TODO client receives credit upon register
        # should this still not happen if we are overloaded?
        self.credits_issued += 1
        client.credits += 1
        self.num_clients += 1
        """
            credit distribution should not be instantaneous, even if there were credits to grant
            to this client.

            It should happen when the control loop runs, every RTT. 
            normally, credits could be sent on the register response, but we don't really have a concept of this here

            the next RTT truly is the soonest that response could arrive regardless
        """

    def client_deregister(self, client):
        # credits yielded by client
        self.credits_issued -= client.credits

        self.clients.remove(client)
        self.num_clients -= 1



