"""
Server script. Takes the client's actions and computes the results, then sends them back.
"""

from network import *
from core.core import Game, EndOfGame
from factions.templars import Templars
import time
from core.enums import IllegalMoveError, Zone


class OverlordService:
    def __init__(self):
        self.networkManager = ServerNetworkManager(self)
        self.networkManager.startServer()

        self.game = Game(Templars, Templars)
        self.game.start()
        self.players = {}

    # actions

    # opcode 0
    def addPlayer(self, addr):
        if len(self.players) < 2:
            self.players[addr] = self.game.players[len(self.players)]
            self.redraw()
        else:
            print "Cannot add more players."

    # opcode 1
    def revealFacedown(self, addr, index):
        pl = self.players[addr]
        try:
            pl.revealFacedown(pl.facedowns[index])
        except IllegalMoveError as e:
            print e
            return
        except IndexOutOfRangeError as e:
            print e
            return
        self.redraw()
        if pl.activeAbility is not None:
            self.requestTarget(addr)

    # opcode 2
    def playFaceup(self, addr, index):
        pl = self.players[addr]
        try:
            pl.playFaceup(pl.hand[index])
        except IllegalMoveError as e:
            print e
            return
        except IndexOutOfRangeError as e:
            print e
            return
        self.redraw()
        if pl.activeAbility is not None:
            self.requestTarget(addr)

    # opcode 3
    def attack(self, addr, cardIndex, targetIndex, targetZone):
        pl = self.players[addr]
        try:
            attacker = pl.faceups[cardIndex]
        except IndexOutOfRangeError as e:
            print e
            return
        if targetZone == Zone.face:
            target = Zone.face
        else:
            target = pl.getEnemy().getCard(targetZone, targetIndex)

        try:
            pl.attack(attacker, target)
        except IllegalMoveError as e:
            print e
        self.redraw()

    # opcode 4
    def play(self, addr, index):
        pl = self.players[addr]
        try:
            pl.play(pl.hand[index])
        except IllegalMoveError as e:
            print e
        except IndexOutOfRangeError as e:
            print e
            return
        self.redraw()

    # opcode 5
    def acceptTarget(self, addr, cardIndex, targetZone, targetIndex):
        pl = self.players[addr]
        try:
            pl.acceptTarget(pl.getEnemy().getCard(targetZone, targetIndex))
        except IllegalMoveError as e:
            print e
        except IndexOutOfRangeError as e:
            print e
            return
        self.redraw()

    # opcode 6
    def endPhase(self, addr):
        try:
            self.players[addr].endPhase()
        except IllegalMoveError as e:
            print e
        self.redraw()

    def requestTarget(self, addr):
        card = self.players[addr].activeAbility.card
        zone = card.zone
        index = self.players[addr].faceups.index(card)  # TODO: other zones

        self.networkManager.sendInts(
            addr,
            ClientNetworkManager.Opcodes.requestTarget,
            zone,
            index
        )

    def redraw(self):
        def getCard(c):
            for i, tc in enumerate(Templars.deck):
                if tc.name == c.name:
                    return i

        for addr, pl in self.players.iteritems():
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerHand,
                *(getCard(c) for c in pl.hand)
                )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFacedowns,
                *(getCard(c) for c in pl.facedowns)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerFaceups,
                *(getCard(c) for c in pl.faceups)
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePlayerManaCap,
                pl.manaCap
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.updatePhase,
                self.game.phase
            )
            self.networkManager.sendInts(
                addr,
                ClientNetworkManager.Opcodes.setActive,
                int(pl.isActivePlayer())
            )

            try:
                enemyPlayer = pl.getEnemy()
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyHand,
                    len(enemyPlayer.hand)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyFacedowns,
                    len(enemyPlayer.facedowns)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyFaceups,
                    *(getCard(c) for c in enemyPlayer.faceups)
                )
                self.networkManager.sendInts(
                    addr,
                    ClientNetworkManager.Opcodes.updateEnemyManaCap,
                    enemyPlayer.manaCap
                )
            except IndexError:
                pass

    def endGame(self, winner):
        for addr, pl in self.players.iteritems():
            if pl == winner:
                opcode = ClientNetworkManager.Opcodes.win
            else:
                opcode = ClientNetworkManager.Opcodes.lose

            self.networkManager.sendInts(
                addr,
                opcode
            )

if __name__ == "__main__":
    service = OverlordService()
    i = 0
    while 1:
        try:
            service.networkManager.recv()
        except EndOfGame as e:
            service.endGame(e.winner)
            break

        i = (i+1) % 100
        if i == 0:
            service.networkManager.sendUnrecievedPackets()
        time.sleep(0.01)
