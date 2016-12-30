"""
Server script. Takes the client's actions and computes the results, then sends them back.
"""

from ServerNetworkManager import ServerNetworkManager
from ClientNetworkManager import ClientNetworkManager
from Player import Player
from enums import *
from Templars import Templars
import time


class OverlordService:
    def __init__(self):
        self.networkManager = ServerNetworkManager(self)
        self.networkManager.startServer()

        self.turn = Turn.p1
        self.phase = Phase.reveal

        self.players = []

        self.targetCallbacks = {}

    def getPlayer(self, addr):
        for pl in self.players:
            if pl.addr == addr:
                return pl

    def getActivePlayer(self):
        return self.players[self.turn]

    # actions

    # opcode 0
    def addPlayer(self, addr):
        if len(self.players) < 2:
            p = Player("Player " + str(len(self.players)))
            p.index = len(self.players)
            p.addr = addr
            p.overlordService = self
            self.players.append(p)
            self.redraw()
        else:
            print "Cannot add more players."

    # opcode 1
    def revealFacedown(self, addr, index):
        self.getPlayer(addr).revealFacedown(index)

    # opcode 2
    def playFaceup(self, addr, index):
        self.getPlayer(addr).playFaceup(index)

    # opcode 3
    def attack(self, addr, cardIndex, targetIndex, zone):
        self.getPlayer(addr).attack(cardIndex, targetIndex, zone)

    # opcode 4
    def play(self, addr, index):
        self.getPlayer(addr).play(index)

    # opcode 5
    def acceptTarget(self, addr, cardIndex, targetZone, targetIndex):
        self.getPlayer(addr).acceptTarget(cardIndex, targetZone, targetIndex)

    def endTurn(self):
        player = self.getActivePlayer()
        player.manaCap += 1
        if player.manaCap > 15:
            player.getEnemy().win()
        player.mana = player.manaCap
        print "player " + player.name + " mana cap is " + str(player.manaCap)
        self.turn = Turn.p2 if self.turn == Turn.p1 else Turn.p1
        self.phase = Phase.reveal

    # opcode 6
    def endPhase(self, addr):
        if not self.getPlayer(addr).isActivePlayer():
            print "It is not your turn."
            return

        if self.phase == Phase.reveal:
            self.getActivePlayer().facedowns = []

        self.phase += 1

        if self.phase == Phase.draw:
            self.getActivePlayer().drawCard()
        elif self.phase == Phase.attack:
            for f in self.getActivePlayer().faceups:
                f.hasAttacked = False
        elif self.phase == Phase.play:
            pass
        else:
            self.endTurn()

        self.redraw()

    def getTarget(self, playerKey):
        self.targetCallbacks[playerKey]()

    def destroy(self, card):
        card.moveZone(Zone.graveyard)

    def fight(self, c1, c2):
        if c1.rank < c2.rank:
            self.destroy(c1)
        if c1.rank > c2.rank:
            self.destroy(c2)
        elif c1.rank == c2.rank:
            self.destroy(c1)
            self.destroy(c2)

    def redraw(self):
        def getCard(c):
            for i, tc in enumerate(Templars.deck):
                if tc.name == c.name:
                    return i

        for pl in self.players:
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerHand,
                *(getCard(c) for c in pl.hand)
                )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerFacedowns,
                *(getCard(c) for c in pl.facedowns)
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerFaceups,
                *(getCard(c) for c in pl.faceups)
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePlayerManaCap,
                pl.manaCap
            )
            self.networkManager.sendInts(
                pl.addr,
                ClientNetworkManager.Opcodes.updatePhase,
                self.phase
            )

            try:
                enemyPlayer = pl.getEnemy()
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyHand,
                    len(enemyPlayer.hand)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyFacedowns,
                    len(enemyPlayer.facedowns)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyFaceups,
                    *(getCard(c) for c in enemyPlayer.faceups)
                )
                self.networkManager.sendInts(
                    pl.addr,
                    ClientNetworkManager.Opcodes.updateEnemyManaCap,
                    enemyPlayer.manaCap
                )
            except IndexError:
                pass


if __name__ == "__main__":
    service = OverlordService()
    i = 0
    while 1:
        service.networkManager.recv()
        i = (i+1) % 100
        if i == 0:
            service.networkManager.sendUnrecievedPackets()
        time.sleep(0.01)
