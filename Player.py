"""
Player class.
It has some actions associated with it that the player can take.
A player has the following characteristics:
    Zones
    Mana cap
    Mana
"""
from copy import deepcopy
from random import shuffle
from enums import *
from ClientNetworkManager import ClientNetworkManager
from Templars import Templars

startHandSize = 5
maxManaCap = 15


class Player ():
    def __init__(self, name, faction=Templars):
        self.overlordService = None
        self.addr = None

        self.name = name

        self.hand = []
        self.facedowns = []
        self.faceups = []
        self.deck = deepcopy(faction.deck)
        for card in self.deck:
            card.owner = self
        self.graveyard = []
        self.manaCap = 1
        self.mana = 0

        self.iconPath = faction.iconPath
        self.cardBack = faction.cardBack

        shuffle(self.deck)
        for i in range(0, startHandSize):
            self.drawCard()

        self.targetingCardInstance = None

    def drawCard(self):
        if len(self.deck) != 0:
            c = self.deck.pop()
            c.moveZone(Zone.hand)

    def isActivePlayer(self):
        return self.overlordService.turn == self.index

    def requestTarget(self, card):
        try:
            index = self.faceups.index(card)
            zone = Zone.faceup
        except ValueError:
            try:
                index = self.facedowns.index(card)
                zone = Zone.facedown
            except ValueError:
                pass

        self.overlordService.networkManager.sendInts(
            self.addr,
            ClientNetworkManager.Opcodes.requestTarget,
            zone,
            index
        )

    def getEnemy(self):
        index = 1 if self.overlordService.players[0] == self else 0
        return self.overlordService.players[index]

    def getCard(self, zone, index):
        if zone == Zone.faceup:
            return self.faceups[index]
        elif zone == Zone.facedown:
            return self.facedowns[index]

    def moveCard(self, card, zone):
        if card.zone == Zone.faceup:
            self.faceups.remove(card)
        elif card.zone == Zone.facedown:
            self.facedowns.remove(card)
        elif card.zone == Zone.hand:
            self.hand.remove(card)
        elif card.zone == Zone.graveyard:
            self.graveyard.remove(card)

        if zone == Zone.faceup:
            self.faceups.append(card)
            card.zone = Zone.faceup

            if self.overlordService:
                self.overlordService.redraw()

            card.onSpawn()
        elif zone == Zone.facedown:
            self.facedowns.append(card)
            card.zone = Zone.facedown
        elif zone == Zone.hand:
            self.hand.append(card)
            card.zone = Zone.hand
        elif zone == Zone.graveyard:
            if card.zone == Zone.faceup:
                card.onDeath()
            self.graveyard.append(card)
            card.zone = Zone.graveyard

        if self.overlordService:
            self.overlordService.redraw()

    # actions

    def play(self, index):
        if not self.isActivePlayer():
            print "Can only play facedowns during your turn."
        elif self.overlordService.phase != Phase.play:
            print "Can only play facedowns during play phase."
        else:
            card = self.hand[index]
            card.moveZone(Zone.facedown)
            card.hasAttacked = False

    def revealFacedown(self, index):
        if not self.isActivePlayer():
            print "Can only reveal facedowns during your turn."
        elif self.overlordService.phase != Phase.reveal:
            print "Can only reveal facedowns during reveal phase."
        elif self.mana < self.facedowns[index].cost:
            print "Not enough mana."
        else:
            card = self.facedowns[index]
            self.mana -= card.cost
            card.moveZone(Zone.faceup)

    def playFaceup(self, index):
        if not self.isActivePlayer():
            print "Can only play faceups during your turn."
        elif self.overlordService.phase != Phase.reveal:
            print "Can only play faceups during reveal phase."
        elif not self.hand[index].playsFaceUp:
            print "That card does not play face-up."
        elif self.mana < self.hand[index].cost:
            print "Not enough mana."
        else:
            card = self.hand[index]
            self.mana -= card.cost
            card.moveZone(Zone.faceup)

    def attack(self, cardIndex, targetIndex, zone):
        if not self.isActivePlayer():
            print "It is not your turn."
            return

        attacker = self.faceups[cardIndex]

        if attacker.hasAttacked:
            print "Can only attack once per turn."
        else:
            attacker.hasAttacked = True

            enemy = self.getEnemy()
            if zone == Zone.face:
                enemy.manaCap += attacker.rank
                if enemy.manaCap > 15:
                    print "You're winner"
                    self.win()
            elif zone == Zone.faceup:
                try:
                    self.overlordService.fight(enemy.faceups[targetIndex], attacker)
                except IndexError as e:
                    print "Trying to attack card index that does not exist"
            elif zone == Zone.facedown:
                try:
                    self.overlordService.fight(enemy.facedowns[targetIndex], attacker)
                except IndexError as e:
                    print "Trying to attack card index that does not exist"
            else:
                print "Not a recognized zone."

        self.overlordService.redraw()

    def acceptTarget(self, cardIndex, targetZone, targetIndex):
        enemy = self.getEnemy()
        card = self.getCard(Zone.faceup, cardIndex)

        if targetZone == Zone.facedown:
            card.onGetTarget(enemy.facedowns[targetIndex])
        elif targetZone == Zone.faceup:
            card.onGetTarget(enemy.faceups[targetIndex])
        else:
            raise Exception("Bad zone.")

        self.overlordService.redraw()

    def win(self):
        self.overlordService.networkManager.sendInts(
            self.addr,
            ClientNetworkManager.Opcodes.win,
        )
        self.overlordService.networkManager.sendInts(
            self.getEnemy().addr,
            ClientNetworkManager.Opcodes.lose,
        )