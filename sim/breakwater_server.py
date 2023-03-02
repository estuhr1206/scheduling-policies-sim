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
        # update clients to be indices, not actual clients, allowing clients to be identified
        self.available_client_ids = []
        self.AGGRESSIVENESS_ALPHA = ALPHA
        self.BETA = BETA
        self.overcommitment_credits = 0
        self.max_delay = 0

        self.credit_pool_records = []
        self.requests_at_once = []

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

        # if self.num_clients > 0:
        #     self.send_credits(int(credits_to_send))
        # update: credits will now be sent upon task completion to better emulate
        # how breakwater was actually implemented
        if self.state.config.record_credit_pool:
            self.credit_pool_records.append([self.total_credits, self.credits_issued, self.overcommitment_credits])

    def lazy_distribution(self, client_id):
        # hmmmmmmm
        """
            for one client, this is easy and makes sense. We're just changing where the send credit call
            happens

            For multiple clients, it's a bit more hairy.
            Or is it???

            actually, the whole thing is more that we don't really need a "send credit" method
            or at least, not in its current state, choosing random clients and such.

            issue
            if demand is sky high, won't a single client eat up all available credits?
            how does this ever become fair?
            Won't that single client then also have more opportunities (more responses to task
            completions) to get more credits and have a feedback loop?

            TODO but not a big deal for now

        """
        client = self.all_clients[client_id]
        available_credits = self.total_credits - self.credits_issued
        if available_credits > 0:
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         client.credits + (self.total_credits - self.credits_issued))
            if Cx_new - client.credits > 0:
                # client might spend credit immediately, but that's ok
                # TODO technically should be sending multiple at once
                # is it bad that client gets these instantaneously for now?
                self.credits_issued += 1
                client.add_credit()

        elif available_credits < 0:
            # grab calculation from paper
            pass

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
            credits_spent_at_once = 0
            # TODO checking value just in case while still using single client
            requests_at_once_record = [credits_to_send, self.state.all_clients[0].current_demand]
            while i < credits_to_send:
                if self.num_clients <= 0:
                    break
                chosen_client_id = random.choice(self.available_client_ids)
                chosen_client = self.all_clients[chosen_client_id]
                Cx_new = min(chosen_client.current_demand + self.overcommitment_credits,
                             chosen_client.credits + (self.total_credits - self.credits_issued))
                if Cx_new - chosen_client.credits > 0:
                    if chosen_client.add_credit():
                        credits_spent_at_once += 1
                    self.credits_issued += 1
                    i += 1
                else:
                    # TODO for debugging purposes, client de registering is off right now
                    # if our single client doesn't get any credits, just stop
                    break
            # maybe record this, but maybe also record
            # maybe just recording client demand? like all the time?
            # that's too much, every RTT maybe?
            if self.state.config.record_requests_at_once:
                requests_at_once_record.append(credits_spent_at_once)
                self.requests_at_once.append(requests_at_once_record)

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
                chosen_client_id = random.choice(self.available_client_ids)
                chosen_client = self.all_clients[chosen_client_id]
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
        self.clients.append(client.id)
        # TODO should this still happen if we are overloaded?
        self.credits_issued += 1
        # client.credits += 1
        # now, client should be allowed to spend this credit
        client.add_credit()
        self.num_clients += 1

    def client_deregister(self, client):
        # credits yielded by client
        self.credits_issued -= client.credits

        self.clients.remove(client.id)
        self.num_clients -= 1



