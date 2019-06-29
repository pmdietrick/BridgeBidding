import random
import matplotlib.pyplot as plt

def main():
    dataX = []
    dataY = []
    iterations = 1000
    
    openersX = {}
    openersY = {}
    #openers = ['1 C', '1 D', '1 H', '1 S', '1 N', '2 C', '2 D', '2 H', '2 S', '2 N']
    openers = ['1 C', '1 D', '1 H', '1 S', '1 N']
    for bid in openers:
        openersX[bid] = []
        openersY[bid] = []
    
    for i in range(iterations):
        rowX, rowY, openingBid, score, openingHcp = newGame()
        dataX.append(rowX)
        dataY.append(rowY)
        
        for bid in openers:
            if bid == openingBid:
                openersX[bid].append(openingHcp)
                openersY[bid].append(score)
    
    fig = plt.figure(figsize=(16,10))
    i=0
    for bid in openers:
        i += 1
        plt.subplot(2, 3, i)
        plt.scatter(openersX[bid], openersY[bid], alpha = .1)
        plt.title(bid)
        plt.xlabel('HCP')
        plt.ylabel('Score')
        
    plt.show()
    
    
    with open('bids.txt', 'w') as filehandle:  
        filehandle.writelines("%s\n" % bid for bid in dataX)
    filehandle.close()
    
    with open('features.txt', 'w') as filehandle:  
        filehandle.writelines("%s\n" % feature for feature in dataY)
    filehandle.close()
    
    
def newGame():
    print("\n Creating a deck of cards and shuffling it...\n")
    
    d1 = Deck()
    d1.shuffle()
    
    s = Hand(label = "south")
    n = Hand(label = "north")
    e = Hand(label = "east")
    w = Hand(label = "west")
    
    seats = [e,w,s,n]
    
    for p in seats:
        for i in range(13):
            c = d1.deal()
            p.add(c)
        #print(p.showHand())
        print(p.label)
        p.HCP()
        p.suitLengths()
        
    south = Bidder(s, 0)
    north = Bidder(n, 1)
    
    bids = auction(south, north)
    
    contract = bids[len(bids)-2]
    if contract == [0, 'P']:
        score = 0
    else:
        score = getScore(south.hand, north.hand, contract[1], contract[0])
    
    if bids[0] == [0, 'P']:
        openingBid = bids[1]
        openingHcp = north.hand.hcp
    else:
        openingBid = bids[0]
        openingHcp = south.hand.hcp
    openingBid[0] = str(openingBid[0])
    openingBid = ' '.join(openingBid)
    print("open", openingBid, openingHcp)
    
    #file output
    while len(bids) < 10:
        bids.append([0, 'P'])
    while len(bids) > 10:
        bids.pop()
    features = [south.hand.hcp, south.hand.clubs, south.hand.diamonds, south.hand.hearts, south.hand.spades]
    return bids, features, openingBid, score, openingHcp

def getScore(hand1, hand2, trump, tricks):
    hcp = hand1.hcp + hand2.hcp
    tricksWon = round(hcp/3 + random.random())
    if trump == 'N':
        score = 30*(tricksWon-6) + 10
        gamescore = 30*min(tricksWon-6, tricks) + 10
    elif trump == 'S' or trump == 'H':
        ruffs = hand1.sLengths[trump] + hand2.sLengths[trump] - 7
        tricksWon += ruffs
        score = 30*(tricksWon-6)
        gamescore = 30*min(tricksWon-6, tricks)
    else:
        ruffs = hand1.sLengths[trump] + hand2.sLengths[trump] - 7
        tricksWon += ruffs
        score = 20*(tricksWon-6)
        gamescore = 10*min(tricksWon-6, tricks)
        
    if tricksWon < (tricks + 6):
        score = -50 * (tricks + 6 - tricksWon)
        
    if score >= 100 and gamescore >= 100:
        score += 100
        
    if tricksWon >= 12 and tricks >= 12:
        score += 500
        
    if tricksWon == 13 and tricks == 13:
        score += 250
        
    return score

def auction(south, north):
    bid = [-1, 0]
    lastBid = [-1, 0]
    player = south
    waiting = north
    bids = []
    
    #Both players get a chance to bid, then bidding continues until pass
    while bid != [0, 'P'] or player.bids == []:
        
        bid = player.bid(lastBid)
        print(bid)
        waiting.infer(bid)
        
        bids.append(bid)
        
        lastBid = bid
        
        if player == south:
            player = north
            waiting = south
        else:
            player = south
            waiting = north
        
    return bids
        

class Bidder(object):
    
    def __init__(self, hand, name):
        self.name = name
        self.hand = hand
        #hcp range
        self.pRange = [0, 40 - self.hand.hcp]
        #suit range
        self.pS = [0, 13]
        self.pH = [0, 13]
        self.pD = [0, 13]
        self.pC = [0, 13]
        self.pLengths = {'C' : self.pC, 'D' : self.pD, 'H' : self.pH, 'S' : self.pS}
        self.NT_OPEN = True
        self.pts = self.points()
        self.pBids = []
        self.bids = []
    
    def infer(self, bid):
        self.pBids.append(bid)
        #todo: update pRange according to the constraints of the bid
    
    def bid(self, lastBid):
        hcp = self.hand.hcp
        hcpMin = self.getHcpMin()
        SUITS = ['C', 'D', 'H', 'S']
        bid = [0, 'P']
        
        
        #opening bids
        if self.nonpassBids(self.pBids) == 0 and self.nonpassBids(self.bids) == 0:
            if hcp >=15 and hcp <= 17 and self.NT_OPEN:
                bid = [1, 'N']
            elif hcp >=20 and hcp <= 22 and self.NT_OPEN:
                bid = [2, 'N']
            elif hcp >= 20:
                tricks = 2
                suit = self.getOpenSuit()
                bid = [tricks, suit]
            #5 card major, longest suit
            elif hcp >=11 and hcp <= 19:
                tricks = 1
                suit = self.getOpenSuit()
                bid = [tricks, suit]
                    
        #first responses
        elif self.nonpassBids(self.bids) == 0:
            if hcp >= 12 and hcp <= 16:
                bid = self.respond(lastBid, 1)
            elif hcp >= 17:
                bid = self.respond(lastBid, 2)
            elif hcp >= 5 or hcpMin >= 22:
                bid = self.respond(lastBid)
        #responses
        else:
            bid = self.respond(lastBid)
            maxBid = 1
            if hcpMin >= 17 and hcpMin <= 19:
                maxBid = 2
            elif hcpMin >= 20 and hcpMin <= 22:
                maxBid = 3
            elif hcpMin >= 23 and hcpMin <= 28:
                maxBid = 4
            elif hcpMin >= 29 and hcpMin <= 32:
                maxBid = 5
            elif hcpMin >= 33 and hcpMin <= 36:
                maxBid = 6
            elif hcpMin >= 37:
                maxBid = 7
                
            if bid[0] <= maxBid:
                self.bids.append(bid)
                return bid
            else:
                bid = [0, 'P']
                self.bids.append(bid)
                return bid
            
        self.bids.append(bid)
        return bid
    
    def respond(self, lastbid, offset = 0):
        bidOrder = ['C', 'D', 'H', 'S', 'N']
        longSuit = 'N'
        tricks = lastbid[0] + offset
        TARGET = 8
        
        for suit in self.pLengths:
            total_len = self.hand.sLengths[suit] + self.pLengths[suit][0]
            if self.pLengths[suit][0] >= 5 and total_len >= TARGET:
                longSuit = suit
                
        if longSuit == 'N':
            for suit in self.pLengths:
                if self.hand.sLengths[suit] >= 5 and self.pLengths[suit][1] + self.hand.sLengths[suit] >= TARGET:
                    longSuit = suit
        
        #bid higher tricks unless suit is higher; bids must increase
        for suit in bidOrder:
            if suit == longSuit:
                tricks += 1
                break
            if suit == lastbid[1]:
                break
                
        return [tricks, longSuit]
    
    def getOpenSuit(self):
        if self.hand.sLengths['S'] >= 5 and self.hand.sLengths['H'] <= self.hand.sLengths['S']:
            return 'S'
        elif self.hand.sLengths['H'] >= 5:
            return 'H'
        elif self.hand.sLengths['D'] >= self.hand.sLengths['C']:
            return 'D'
        else:
            return 'C'
            
        
    def points(self):
        SUITS = ['C', 'D', 'H', 'S']
        self.pts = self.hand.hcp
        
        for suit in SUITS:
            if self.hand.sLengths[suit] <= 3:
                self.pts += 3 - self.hand.sLengths[suit]
            if self.hand.sLengths[suit] <= 1 or self.hand.sLengths[suit] >= 6:
                self.NT_OPEN = False
    
    def getHcpMin(self):
        return self.hand.hcp + self.pRange[0]
    
    def nonpassBids(self, bids):
        count = 0
        for bid in bids:
            if bid != [0, 'P']:
                count += 1
        return count
    

class Hand(object):

    """A labeled collection of cards that can be sorted"""

    #------------------------------------------------------------

    def __init__(self, label=""):

        """Create an empty collection with the given label."""

        self.label = label
        self.cards = []
        self.hcp = 0
        self.spades = 0
        self.hearts = 0
        self.diamonds = 0
        self.clubs = 0
        self.sLengths = {'C' : self.clubs, 'D' : self.diamonds, 'H' : self.hearts, 'S' : self.spades}

    #------------------------------------------------------------

    def add(self, card):
        
        """ Add card to the hand """

        self.cards.append(card)

    #------------------------------------------------------------

    def sort(self):
        
        """ Arrange the cards in descending bridge order."""

        self.cards.sort()
        self.cards.reverse()

    #------------------------------------------------------------

    def showHand(self):
        
        print(self.label + "'s Cards:")
        for suit in Card.SUITS:
            card_string = []
            for c in self.cards:
                if suit == c.suitName():
                    card_string.append(c.rankName() + c.suitName())
            print(*card_string)
            
    def HCP(self):
        hcp = 0
        for c in self.cards:
            if c.rank() >= 11:
                hcp += c.rank() - 10
                
        print('HCP: ', hcp)
        self.hcp = hcp
        
    def suitLengths(self):
        s = 0
        h = 0
        d = 0
        c = 0
        
        for card in self.cards:
            if card.suit() == 'C':
                c += 1
            if card.suit() == 'D':
                d += 1
            if card.suit() == 'H':
                h += 1
            if card.suit() == 'S':
                s += 1
                
        print('Suit lengths: ', c, d, h, s)
        print()
        
        self.spades = s
        self.hearts = h
        self.diamonds = d
        self.clubs = c
        self.sLengths = {'C' : self.clubs, 'D' : self.diamonds, 'H' : self.hearts, 'S' : self.spades}
        

class Card(object):
    '''A simple playing card. A Card is characterized by two components:
    rank: an integer value in the range 1-13, inclusive (Ace-King)
    suit: a character in 'cdhs' for clubs, diamonds, hearts, and
    spades.'''

    SUITS = 'CDHS'
    SUIT_NAMES = ['C', 'D', 'H', 'S']

    RANKS = list(range(2,15))
    RANK_NAMES = ['2', '3', '4', '5', '6',
                  '7', '8', '9', '10', 
                  'J', 'Q', 'K', 'A']

    def __init__(self, rank, suit):
        self.rank_num = rank
        self.suit_char = suit
        
    def suit(self):
        '''Card suit
        post: Returns the suit of self as a single character'''

        return self.suit_char

    def rank(self):
        '''Card rank
        post: Returns the rank of self as an int'''

        return self.rank_num
        
    def suitName(self):
        '''Card suit name
        post: Returns one of ('clubs', 'diamonds', 'hearts',
              'spades') corrresponding to self's suit.'''

        index = self.SUITS.index(self.suit_char)
        return self.SUIT_NAMES[index]        

    def rankName(self):
        index = self.RANKS.index(self.rank_num)
        return self.RANK_NAMES[index]

    def __str__(self):
        '''String representation
        post: Returns string representing self, e.g. 'Ace of Spades' '''

        return self.rankName() + self.suitName()


class Deck(object):

    #------------------------------------------------------------

    def __init__(self):

        cards = []
        for suit in Card.SUITS:
            for rank in Card.RANKS:
                cards.append(Card(rank,suit))
        self.cards = cards # cards in the deck
        self._size = 52 # number of cards initally in a deck

    #------------------------------------------------------------

    def size(self):

        """Cards left, Theta(1) run-time efficiency
        post: Returns the number of cards in self"""
        
        return self._size

    #------------------------------------------------------------

    def deal(self):

        """Deal a single card, Theta(1) run-time efficiency
        pre:  self.size() > 0
        post: Returns the next card in self, and removes it from self."""

        assert self._size > 0

        card = self.cards.pop() # removing a card from the deck
        self._size -= 1 # update the number of cards in the deck
        
        return card

    #------------------------------------------------------------

    def shuffle(self):

        """Shuffles the deck, using Python's random module
        post: randomizes the order of cards in self"""

        random.shuffle(self.cards)

        #n = self._size()
        #cards = self.cards
        #for i,card in enumerate(cards):
        #    pos = randrange(i,n)
        #    cards[i] = cards[pos]
        #    cards[pos] = card

    #------------------------------------------------------------

    def addTop(self,card):

        """ adds a card to the top of the deck, Theta(1) run-time efficiency
        pre: card is of type Card
        post: card is added back to the top of the deck"""

        self.cards.append(card) # putting the card to the top of the deck
        self._size += 1 # incrementing the size of the deck

    #------------------------------------------------------------

    def addRandom(self,card):

        """ adds a card to the random place in the deck, Theta(1) run-time efficiency
        pre: card is of type Card
        post: card is added back to the deck, into random place"""

        place = random.randint(0,self._size) # getting a random position for the card to be place into
        self.cards.insert(place,card) # putting the card into place position in the deck
        self._size += 1 # incrementing the size of the deck

    #------------------------------------------------------------

    def addBottom(self,card):

        """ adds a card to the bottom of the deck, Theta(1) run-time efficiency
        pre: card is of type Card
        post: card is added back to the bottom of the deck"""
        
        self.cards.insert(0,card) # put the card to the bottom of the deck
        self._size += 1 # increment size of the deck


        

main()
