from factions.base import *
from tests.dummyFaction import dummyFactionPlayer
from core.core import Game


def testSweep():
    game = Game(
        dummyFactionPlayer([sweep()]),
        dummyFactionPlayer([one(), one(), one()]))
    p1 = game.players[0]
    p2 = game.players[1]

    p1.endPhase()
    p1.play(p1.hand[0])
    p1.endPhase()

    # play 2 cards face-up and 1 face-down
    for c in p2.hand[:-1]:
        c.cost = 0
        c.playsFaceup = True
        p2.playFaceup(c)
    p2.endPhase()
    p2.play(p2.hand[0])
    p2.endPhase()

    p1.mana = 4
    p1.revealFacedown(p1.facedowns[0])

    assert len(p2.faceups) == 0
    assert len(p2.facedowns) == 1
