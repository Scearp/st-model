import csv

def weak(party_votes, total_votes, max_weak):
    if party_votes / total_votes >= max_weak:
        return total_votes * max_weak
    else:
        return party_votes

class Constituency:
    def __init__(self, election, column):
        self.election = election
        self.name = self.election.data[0][column]
        self.weight = self.election.data[1][column] # usually = 1; > 1 for electoral college, etc.
        votes = [int(row[column]) for row in self.election.data[2:]]

        self.votes = [float(votes[p] + sum(votes) * self.election.adjust[p]) for p in range(len(votes))]
        for i in range(len(self.votes)):
            if self.votes[i] < 0:
                self.votes[i] = 0
        self.weak_votes = [weak(self.votes[party], sum(self.votes), 0.2)
                            for party in range(len(self.votes))]
        self.strong_votes = [self.votes[party] - self.weak_votes[party]
                                for party in range(len(self.votes))]

    def project(self):
        self.projected_weak = [0] * len(self.votes)
        self.projected_strong = [0] * len(self.votes)
        self.projected_votes = [0] * len(self.votes)

        for party in range(len(self.votes)):
            self.projected_weak[party] = self.weak_votes[party] * self.election.weak_change[party]
            self.projected_strong[party] = self.strong_votes[party] * self.election.strong_change[party]
            self.projected_votes[party] = self.projected_weak[party] + self.projected_strong[party]
        proj_sorted = sorted(list(self.projected_votes))
        self.winner = self.projected_votes.index(proj_sorted[-1])
        self.runner_up = self.projected_votes.index(proj_sorted[-2])
        self.rate()

    def rate(self):
        self.margin = float(self.projected_votes[self.winner] - self.projected_votes[self.runner_up]) / sum(self.projected_votes)
        self.rating = ""
        if self.margin <= .01:
            self.rating = "TILT"
        elif self.margin > .01 and self.margin <= .05:
            self.rating = "LEAN"
        elif self.margin > .05 and self.margin <= .10:
            self.rating = "LIKELY"
        else:
            self.rating = "SAFE"


class Election:
    def __init__(self, data_file, adjust=[0,0,0,0,0]):
        self.file = data_file
        self.adjust = adjust
        with open(data_file) as csv_file:
            reader = csv.reader(csv_file, delimiter=',')
            self.data = [list(line) for line in reader]
        self.parties = [row[0] for row in self.data[2:]]
        self.constituencies = [Constituency(self, x)
                                for x in range(1, len(self.data[0]))]
        self.total_votes = sum([sum(c.votes) for c in self.constituencies])
        self.weak_vote_shares = [sum([c.weak_votes[party] / self.total_votes
                                    for c in self.constituencies])
                                        for party in range(len(self.parties))]
        self.strong_vote_shares = [sum([c.strong_votes[party] / self.total_votes
                                    for c in self.constituencies])
                                        for party in range(len(self.parties))]

    def project(self, projected_vote_shares):
        self.weak_change = [1.0] * len(self.parties)
        self.strong_change = [1.0] * len(self.parties)

        for party in range(len(self.parties)):
            if projected_vote_shares[party] >= self.strong_vote_shares[party]:
                self.strong_change[party] = 1.0
                self.weak_change[party] = ((projected_vote_shares[party]
                                            - self.strong_vote_shares[party])
                                                / self.weak_vote_shares[party])
            else:
                try:
                    self.strong_change[party] = projected_vote_shares[party] / self.strong_vote_shares[party]
                except:
                    self.strong_change[party] = 0.0
                self.weak_change[party] = 0.0
        
        for c in self.constituencies:
            c.project()

def write_svg(winners, margins, colours, oldmap = "./maps/map.svg", newmap = "./newmap.svg", r = 5):
    map_base = open(oldmap).readlines()
    with open(newmap, "w") as map_new:
        for f in map_base[:r]:
            map_new.write(f)
        for c in margins:
            try:
                map_new.write(('#%s{fill:#%s;}\n' % (c.replace('0',''), colours[winners[c]][margins[c]])))
            except:
                pass
        for f in map_base[r:]:
            map_new.write(f)
    map_new.close()
    