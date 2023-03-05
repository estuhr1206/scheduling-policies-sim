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

        # TODO debugging
        self.debug_records = []

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

        # TODO debugging on single client
        # i think this every rtt could be considered "explicit" as needed
        if self.num_clients > 0:
            #self.send_credits(int(credits_to_send))
            self.lazy_distribution(0)
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
        client = self.state.all_clients[client_id]
        available_credits = self.total_credits - self.credits_issued
        # Cx_new = 0
        Cx = client.c_unused + client.c_in_use
        if available_credits > 0:
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx + available_credits)

        elif available_credits < 0:
            # grab calculation from paper
            # demand + overcommitment is at least 1 (with 0 demand)
            # what if client is already at 0 credits?
            Cx_new = min(client.current_demand + self.overcommitment_credits,
                         Cx - 1)
        else:
            # no credit updates needed
            return
        # possible for both situations to result in adding or subtracting credits, depending on
        # demand/pool?

        credits_to_send = Cx_new - Cx
        # TODO debugging
        debug = [self.state.timer.get_time(), credits_to_send, Cx_new, Cx, client.current_demand, client_id]
        self.debug_records.append(debug)
        self.send_credits_lazy(client, credits_to_send)

    def send_credits_lazy(self, client, credits_to_send):
        # TODO not a real concept of "coalescing messages" here
        # this will result in this code running for every single task: might add significant time to sim
        if credits_to_send > 0:
            # client might spend credit immediately, but that's ok
            # is it bad that client gets these instantaneously for now? no RTT
            credits_spent_at_once = 0
            requests_at_once_record = [credits_to_send, client.current_demand]
            for i in range(credits_to_send):
                self.credits_issued += 1
                if client.add_credit():
                    credits_spent_at_once += 1
            # this might be a bad record. Can happen for every single task....
            if self.state.config.record_requests_at_once:
                requests_at_once_record.append(credits_spent_at_once)
                self.requests_at_once.append(requests_at_once_record)
        elif credits_to_send < 0:
            credits_to_revoke = -credits_to_send
            if client.c_unused < credits_to_revoke:
                self.credits_issued -= client.c_unused
                client.c_unused = 0
            else:
                client.c_unused -= credits_to_revoke
                self.credits_issued -= credits_to_revoke

    def client_register(self, client):
        self.available_client_ids.append(client.id)
        # TODO should this still happen if we are overloaded?
        self.credits_issued += 1
        # now, client should be allowed to spend this credit
        client.add_credit()
        self.num_clients += 1

    def client_deregister(self, client):
        # credits yielded by client
        self.credits_issued -= client.c_unused

        self.available_client_ids.remove(client.id)
        self.num_clients -= 1



